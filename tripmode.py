import time
import struct
import itertools
from enum import Enum

from panda import Panda


class DriveMode(Enum):
    """Drive mode enumeration."""
    NORMAL = 0
    SPORT = 1
    MOUNTAIN = 2
    HOLD = 3


class CarState:
    """Store the current speed and drive mode."""
    def __init__(self, p: Panda):
        self.speed_threshold = 50
        self.speed = 0
        self.panda = p
        self.modes = itertools.cycle(DriveMode)
        self.mode = self.modes.__next__()  # Call next once to get it to NORMAL
        self.mode_select_timeout = None

    def _next_mode(self) -> DriveMode:
        self.mode = self.modes.__next__()
        return self.mode

    def _mode_button_press(self):
        """The mode button is pressed."""
        if self.mode_select_timeout is None:
            # First press just brings up mode selection which times out after 3 seconds with no input
            self.mode_select_timeout = time.perf_counter() + 3
            return

        # Each subsequent press gives us more time
        self.mode_select_timeout = time.perf_counter() + 3

        # And changes the selected mode
        self._next_mode()
        print("Mode is: ", self.mode)

    def _set_speed(self, speed):
        """Set the current speed and trigger actions."""
        prior_speed = self.speed
        self.speed = speed
        # TODO: Add a mode switch cooldown
        if prior_speed < self.speed_threshold and self.speed > self.speed_threshold:
            print(f"Switch to HOLD mode. Current speed {self.speed}")
        if prior_speed >= self.speed_threshold and self.speed <= self.speed_threshold:
            print(f"Switch to NORMAL mode. Current speed {self.speed}")

    def update(self, addr, dat):
        """Update the state from CAN messages."""
        if self.mode_select_timeout and time.perf_counter() >= self.mode_select_timeout:
            self.mode_select_timeout = None
            print("Mode set: ", self.mode)

        if addr == 0x3e9:  # Speed is 1001 (0x3e9 hex)
            # '!' for big-endian. H for unsigned short (since it's 16 bits or 2 bytes)
            # divide by 100.0 b/c factor is 0.01
            self._set_speed(struct.unpack("!H", dat[:2])[0] / 100.0)
        elif addr == 0x1e1:  # ASCMSteeringButton
            # Check if the 7th bit of byte 4 is a 1
            if int(dat[4]) >> 7 & 1:
                self._mode_button_press()


def can_recv(p: Panda, s: CarState) -> None:
    """Read the CAN messages and parse out the vehicle speed and mode button presses."""
    for addr, _, dat, _src in p.can_recv():
        s.update(addr, dat)


def main() -> None:
    """Entry Point. Monitor Chevy volt speed."""
    try:
        p = Panda()
    except Exception as exc:
        print(f"Failed to connect to Panda! {exc}")
        return

    s = CarState()

    try:
        while True:
            can_recv(p, s)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        p.close()


if __name__ == "__main__":
    main()