import struct

from panda import Panda

CURRENT_SPEED = 0.0


def read_vehicle_speed(p: Panda) -> None:
    """Read the CAN messages and parse out the vehicle speed."""
    global CURRENT_SPEED

    for addr, _, dat, _src in p.can_recv():
        if addr == 0x3e9:  # Speed is 1001 (0x3e9 hex)
            # '!' for big-endian. H for unsigned short (since it's 16 bits or 2 bytes)
            # divide by 100.0 b/c factor is 0.01
            CURRENT_SPEED = struct.unpack("!H", dat[:2])[0] / 100.0

        # Just keep updating the same line
        print(f"\rSpeed: {int(CURRENT_SPEED):03d}", end="")


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
    finally:
        p.close()


if __name__ == "__main__":
    main()