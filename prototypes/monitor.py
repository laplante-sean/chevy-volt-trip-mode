import sys
import struct

from panda import Panda

CURRENT_SPEED = 0.0
BUTTON = 0
PRESS_COUNT = 0


def read_vehicle_speed(p: Panda) -> None:
    """Read the CAN messages and parse out the vehicle speed."""
    global CURRENT_SPEED
    global BUTTON
    global PRESS_COUNT

    for addr, _, dat, _src in p.can_recv():
        if addr == 0x3e9:  # Speed is 1001 (0x3e9 hex)
            # '!' for big-endian. H for unsigned short (since it's 16 bits or 2 bytes)
            # divide by 100.0 b/c factor is 0.01
            CURRENT_SPEED = struct.unpack("!H", dat[:2])[0] / 100.0
        elif addr == 0x1e1:  # ASCMSteeringButton
            # Check if the 7th bit of byte 4 is a 1
            if int(dat[4]) >> 7 & 1:
                BUTTON = 1
            elif BUTTON == 1:
                # Increment the press count on button release
                PRESS_COUNT += 1
                BUTTON = 0
            else:
                BUTTON = 0

        # Just keep updating the same line
        sys.stdout.write(f"\rSpeed: {int(CURRENT_SPEED):03d} Button: {BUTTON}")
        sys.stdout.flush()


def main() -> None:
    """Entry Point. Monitor Chevy volt speed."""
    try:
        p = Panda()
    except Exception as exc:
        print(f"Failed to connect to Panda! {exc}")
        return

    try:
        while True:
            read_vehicle_speed(p)
    except KeyboardInterrupt:
        print("Exiting...")
        print("Press count: ", PRESS_COUNT)  # Should be the same number of times we pressed it.
    finally:
        p.close()


if __name__ == "__main__":
    main()