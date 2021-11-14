#!/usr/bin/python
"""Chevy Volt trip mode."""
import os
import time
import struct
from typing import List, Union

from panda import Panda
import PySimpleGUI as sg

DEFAULT_SPEED_THRESHOLD = 50


class CarState:
    """Store the current speed and drive mode."""

    #: Cooldown for mode switching
    MODE_SWITCH_COOLDOWN = 60.0
    #: Don't press the button too fast
    BUTTON_PRESS_COOLDOWN = 0.5
    #: Available drive modes in order
    DRIVE_MODES = ["NORMAL", "SPORT", "MOUNTAIN", "HOLD"]
    #: Message ID for the drive mode button
    MSG_ID = 0x1e1
    #: How many packets containing the button press to send at once
    SEND_CLUSTER_SIZE = 50
    #: Mode button press message
    PRESS_MSG = bytearray(b'\x00\x00\x00\x00\x80\x00\x00')

    def __init__(self, p: Panda):
        """Set up the car state."""
        self.speed_threshold = DEFAULT_SPEED_THRESHOLD
        self.speed = 0
        self.panda = p
        self.allow_mode_switch_after = time.perf_counter() + self.MODE_SWITCH_COOLDOWN
        self.allow_button_press_after = 0
        self.mode = "NORMAL"
        self.pending_sends: List[List[List[Union[bytearray, int, None]]]] = []

    def increase_speed_threshold(self, amnt: int = 5):
        """Increase the speed threshold."""
        self.speed_threshold += amnt
        if self.speed_threshold > 70:
            self.speed_threshold = 70

    def decrease_speed_threshold(self, amnt: int = 5):
        """Decrease the speed threshold."""
        self.speed_threshold -= amnt
        if self.speed_threshold < 40:
            self.speed_threshold = 40

    def __del__(self):
        self.close()

    def _switch_modes(self, new_mode: str) -> None:
        """Send the messages needed to switch modes if past our cooldown."""
        now = time.perf_counter()
        if now <= self.allow_mode_switch_after:
            return

        print(f"Switch to {new_mode} mode. Speed: {self.speed}")

        # Update our cooldown and mode
        self.allow_mode_switch_after = now + self.MODE_SWITCH_COOLDOWN
        self.mode = new_mode

        # Required presses starts at 1 (to activate the screen) and
        # mode selection always starts on NORMAL.
        required_presses = 1 + self.DRIVE_MODES.index(new_mode)
        for _ in range(required_presses):
            cluster = []
            for _inner in range(self.SEND_CLUSTER_SIZE):
                cluster.append([self.MSG_ID, None, self.PRESS_MSG, 0])
            self.pending_sends.append(cluster)

    def _set_speed(self, speed):
        """Set the current speed and trigger mode changes."""
        speed = int(speed)
        if self.speed > self.speed_threshold and speed < 1:
            # HACK: Speed jumps to 0 b/w valid values.
            # This hack should handle it.
            return

        self.speed = speed
        if self.speed > self.speed_threshold and self.mode == "NORMAL":
            self._switch_modes("HOLD")
        elif self.speed <= self.speed_threshold and self.mode == "HOLD":
            self._switch_modes("NORMAL")

    def update(self):
        """Update the state from CAN messages."""
        for addr, _, dat, _src in self.panda.can_recv():
            if addr == 0x3e9:  # Speed is 1001 (0x3e9 hex)
                # '!' for big-endian. H for unsigned short (since it's 16 bits or 2 bytes)
                # divide by 100.0 b/c factor is 0.01
                self._set_speed(struct.unpack("!H", dat[:2])[0] / 100.0)

            now = time.perf_counter()
            if self.pending_sends and now > self.allow_button_press_after:
                self.allow_button_press_after = now + self.BUTTON_PRESS_COOLDOWN
                send = self.pending_sends.pop(0)
                self.panda.can_send_many(send)

    def close(self):
        if self.panda:
            self.panda.close()
            self.panda = None


def enable() -> CarState:
    """Enable trip mode."""
    os.system("sudo udevadm trigger")

    try:
        p = Panda()
        p.set_safety_mode(Panda.SAFETY_ALLOUTPUT)  # Turn off all safety preventing sends
        p.set_can_enable(0, True)  # Enable bus 0 for output
        p.can_clear(0xFFFF)  # Flush the panda CAN buffers
    except Exception as exc:
        print(f"Failed to connect to Panda: {exc}")
        return None

    return CarState(p)


def main() -> None:
    """Entry Point. Monitor Chevy volt speed."""
    trip_mode_enabled = False
    car_state = None

    # Theme and layout for the window
    sg.theme('DarkAmber')
    layout = [
        [sg.Button('/\\', font=("Times New Roman", 96)), sg.Text('TRIP MODE', font=("Times New Roman", 66))],
        [sg.Text(size=(2, 1), key='-THRESH-', font=("Times New Roman", 96)), sg.Button('ON', font=("Times New Roman", 96)), sg.Button('OFF', font=("Times New Roman", 96))],
        [sg.Button('\\/', font=("Times New Roman", 96)), sg.Output(size=(40, 10), font=('Consolas 11')), sg.Button('Exit', font=("Times New Roman", 32))]
    ]

    # Create the Window (800x480 is Raspberry Pi touchscreen resolution)
    window = sg.Window(
        'Trip Mode', layout, finalize=True,
        keep_on_top=True, no_titlebar=True,
        location=(0, 0), size=(800, 480),
        element_justification='c')
    window.maximize()  # Make it fullscreen
    window['OFF'].update(disabled=True)  # Start with the off button disabled
    window['/\\'].update(disabled=True)
    window['\\/'].update(disabled=True)

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, _values = window.read(timeout=0)  # Return immediately
        if event == sg.WIN_CLOSED or event == "Exit":
            print("Exiting...")
            if car_state:
                car_state.close()
            break

        # Disable both buttons if either of them are pressed
        if event == "ON" or event == "OFF":
            window['ON'].update(disabled=True)
            window['OFF'].update(disabled=True)
            window['/\\'].update(disabled=True)
            window['\\/'].update(disabled=True)

        # Then perform the action and re-enable the
        # correct action.
        if event == "ON" and not trip_mode_enabled:
            car_state = enable()
            if car_state:
                trip_mode_enabled = True
                window['OFF'].update(disabled=False)
                window['/\\'].update(disabled=False)
                window['\\/'].update(disabled=False)
                print("Trip mode enabled!")

        if event == "OFF" and trip_mode_enabled:
            trip_mode_enabled = False
            car_state.close()
            car_state = None
            window['ON'].update(disabled=False)
            print("Trip mode disabled!")

        if event == "/\\" and car_state:
            car_state.increase_speed_threshold()

        if event == "\\/" and car_state:
            car_state.decrease_speed_threshold()

        if car_state:
            car_state.update()
            window['-THRESH-'].update(str(car_state.speed_threshold))
        else:
            window['-THRESH-'].update(str(DEFAULT_SPEED_THRESHOLD))

    window.close()


if __name__ == "__main__":
    main()
