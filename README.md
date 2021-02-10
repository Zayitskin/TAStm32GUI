# TAStm32GUI
A GUI for the TAStm32 device

There are two main applications in this repository: main.py and tasfile.py.

main.py: this is the GUI for controlling the TAStm32. It loads .tas files created either by hand or with tasfile.py and allows for easy modification of various parameters that the TAStm32 takes in order to aid in the syncing of runs on real hardware. It gives out the command associated with the given parameters, and also has a button that sends such a listed run to the TAStm32.

tasfile.py: this is a GUI to assist with the creation of a .tas file. A .tas file is a zipped collection of a .json file that contains information about the run and what parameters it is to be run with, and a movie file that contains the inputs for the run. It can also be used to edit existing .tas files.

NOTE: The application requires scripts from https://github.com/Ownasaurus/TAStm32 in order to properly interface with the TAStm32 device, so as to not reinvent the wheel. They have been included for your convenience, but are not necessarily the most up-to-date version.
