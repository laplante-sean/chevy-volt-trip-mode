# Chevy Volt Trip Mode

I Created a "trip mode" for my Chevy volt using a Raspberry Pi and a Panda from Comma AI to auto switch between "normal" and "hold mode" on long trips. See [the associated blog post](https://seanlaplante.com/2021/11/13/hacking-my-chevy-volt-to-auto-switch-driving-modes-for-efficiency/) for more information, hardware list, and more detailed setup/usage information.

# Installation

_Tested with Python 3.8 64-bit on Raspbian on a Raspberry Pi 4B, connected to a Gray Panda from Comma AI plugged into the OBD-II port on a 2017 Chevy Volt. More details in [the blog post](https://seanlaplante.com/2021/11/13/hacking-my-chevy-volt-to-auto-switch-driving-modes-for-efficiency/)._

1. See the [hardware list](https://seanlaplante.com/2021/11/13/hacking-my-chevy-volt-to-auto-switch-driving-modes-for-efficiency/) from the associated blog post for more information on required hardware and installation.
1. On a Raspberry Pi with Python 3.8 and Raspbian, create a virtual environment: `python -m venv ./venv`
1. Activate the environment: `source ./venv/bin/activate`
1. Install the dependencies: `pip install -r requirements.txt`
1. Run the app: `python tripmode.py`

## Auto-Start

1. Create the file `/etc/xdg/autostart/tripmode.desktop`
2. Add the contents:

  ```
  [Desktop Entry]
  
  Name=ChevyVoltTripMode
  
  Exec=/usr/bin/python /home/pi/tripmode.py
  ```

3. Reboot

# TODO

1. Create a safety model for the Panda that only allows what we need to be sent on the CAN bus
1. GUI improvements: Bigger buttons, center the GUI
1. `setup.py` and wheel distributions maybe
1. Configurable trigger speed
