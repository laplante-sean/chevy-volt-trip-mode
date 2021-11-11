"""Chevy Volt trip mode."""
import sys
import time
import struct
import logging
from typing import List, Union

from panda import Panda

# Setup basic logging
logging.basicConfig(handlers=[
    logging.FileHandler("tripmode.log"),
    logging.StreamHandler(stream=sys.stdout)])


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

    def __init__(self, p: Panda, debug: bool = False):
        """Set up the car state."""
        self.speed_threshold = 50
        self.speed = 0
        self.panda = p
        self.allow_mode_switch_after = time.perf_counter() + self.MODE_SWITCH_COOLDOWN
        self.allow_button_press_after = 0
        self.mode = "NORMAL"
        self.pending_sends: List[List[List[Union[bytearray, int, None]]]] = []
        self.debug = debug
        if self.debug:
            self.MODE_SWITCH_COOLDOWN = 30.0
            self.allow_mode_switch_after = time.perf_counter()

    def _switch_modes(self, new_mode: str) -> None:
        """Send the messages needed to switch modes if past our cooldown."""
        now = time.perf_counter()
        if now <= self.allow_mode_switch_after:
            return

        logging.info(f"Switch to {new_mode} mode. Speed: {self.speed}")

        # Update our cooldown and mode
        self.allow_mode_switch_after = now + self.MODE_SWITCH_COOLDOWN
        self.mode = new_mode

        # Required presses starts at 1 (to activate the screen) and
        # mode selection always starts on NORMAL.
        required_presses = 1 + self.DRIVE_MODES.index(new_mode)
        logging.debug(f"Needs {required_presses} presses")
        for _ in range(required_presses):
            cluster = []
            for _inner in range(self.SEND_CLUSTER_SIZE):
                cluster.append([self.MSG_ID, None, self.PRESS_MSG, 0])
            self.pending_sends.append(cluster)

    def _set_speed(self, speed):
        """Set the current speed and trigger mode changes."""
        if self.debug:
            if self.mode == "HOLD":
                self._switch_modes("NORMAL")
            elif self.mode == "NORMAL":
                self._switch_modes("HOLD")
            return

        speed = int(speed)
        if self.speed > self.speed_threshold and speed < 1:
            # HACK: Speed jumps to 0 b/w valid values.
            # This hack should handle it.
            return

        self.speed = speed
        if self.speed > self.speed_threshold and self.mode == "NORMAL":
            logging.debug(f"Speed trigger (attempt HOLD): {self.speed}")
            self._switch_modes("HOLD")
        elif self.speed <= self.speed_threshold and self.mode == "HOLD":
            logging.debug(f"Speed trigger (attempt NORMAL): {self.speed}")
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


def main() -> None:
    """Entry Point. Monitor Chevy volt speed."""
    try:
        p = Panda()
        p.set_safety_mode(Panda.SAFETY_ALLOUTPUT)  # Turn off all safety preventing sends
        p.set_can_enable(0, True)  # Enable bus 0 for output
        p.can_clear(0xFFFF)  # Flush the panda CAN buffers
    except Exception as exc:
        logging.error(f"Failed to connect to Panda! {exc}")
        return

    s = CarState(p)

    try:
        while True:
            s.update()
    except KeyboardInterrupt:
        logging.info("Exiting...")
    finally:
        p.close()


if __name__ == "__main__":
    main()
