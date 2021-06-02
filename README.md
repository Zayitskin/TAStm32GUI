# TAStm32GUI
A GUI for the TAStm32 device

The application is divided into two parts: TAS File Creation and TAS Playback.

TAS File Creation assists in the creation of .tas files for use with the TAS Playback. The .tas file contains both descriptive information (name of run, author(s), description) as well as information important for the run (which console it is for, how many controllers, and others).

TAS Playback takes these files and uses them to control a TAStm32 to play the runs back on a real console. It also allows for tweaking the settings to assist with syncing the run. 

NOTE: The application requires scripts from https://github.com/Ownasaurus/TAStm32 in order to properly interface with the TAStm32 device, so as to not reinvent the wheel. They have been included for your convenience, but are not necessarily the most up-to-date version.
