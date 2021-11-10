import time

from panda import Panda


def send_button_press(p: Panda, press_count: int = 2) -> None:
    """Send the ASCMSteering DriveModeButton signal."""
    msg_id = 0x1e1  # 481 decimal
    bus_id = 0
    message = bytearray(b'\x00\x00\x00\x00\x80\x00\x00')  # 0x80 is a 1 in the 7th bit

    for press in range(press_count):
        p.can_send(msg_id, message, bus_id)
        print(f"Sent press {press + 1}")
        time.sleep(1)


def main() -> None:
    """Entry Point. Monitor Chevy volt speed."""
    try:
        p = Panda()
    except Exception as exc:
        print(f"Failed to connect to Panda! {exc}")
        return

    try:
        p.set_safety_mode(Panda.SAFETY_ALLOUTPUT)  # Turn off all safety preventing sends
        p.set_can_enable(0, True)  # Enable bus 0 for output
        p.can_clear(0xFFFF)  # Flush the panda CAN buffers
        while True:
            send_button_press(p)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        p.close()


if __name__ == "__main__":
    main()