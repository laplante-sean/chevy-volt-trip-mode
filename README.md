# Chevy Volt Trip Mode

Create a "trip mode" for Chevy volt using a Raspberry Pi and a Panda from Comma AI to auto switch between "normal" and "hold mode" on long trips. See [the associated blog post]() for more information, hardware list, and more detailed setup/usage information.

# Installation

_Tested with Python 3.8 64-bit on Raspbian on a Raspberry Pi 4B, connected to a Gray Panda from Comma AI plugged into the OBD-II port on a 2017 Chevy Volt. More details in [the blog post]()._

1. See the [hardware list]() from the associated blog post for more information on required hardware and installation.
1. On a Raspberry Pi with Python 3.8 and Raspbian, create a virtual environment: `python -m venv ./venv`
1. Activate the environment: `source ./venv/bin/activate`
1. Install the dependencies: `pip install -r requirements.txt`
1. Run the app: `python tripmode.py`
1. Configure it to run at boot: TODO
