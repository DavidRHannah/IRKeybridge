# Vizio Remote To Keyboard

## My setup
1. Elegoo Uno R3
1. IR Receiver
1. Vizio Remote

## High-Level Overview
The Uno R3 microcontroller is for sending the IR Receiver's digital output from the input of an IR remote (i.e. Vizio remote) to the Serial Output by the virtual COM port (i.e. COM5) so that the data from the receiver can be processed by a python script. Since the Elegoo Uno R3 is not intended to be a HID device ([although it can be made to be](https://github.com/Franzerz/uno-HID-keyboard)), the python script should be running when when using the IR remote.

## Steps For Implementing Yourself
1. Obtain cheap microcontroller and IR receiver
1. Find old Vizio IR remote
1. Flash given firmware onto a microcontroller
1. Setup keybinds in game and/or script
1. Run python script

### Note
- You can generate an executable for yourself to run in the background so you don't have to worry about keeping the python script running by using pyinstaller:
```
pyinstaller --onefile --noconsole --uac-admin=False ir_control.py
```
- You can end the exe by ending the process via Task Manager or by hitting the STOP (x30) key or whatever you program it to be.

You *should* now be able to use your remote! Hopefully...

## Changes
- The current implementation uses the python keyboard library for its precise customization of keyboard commands/inputs.
- The inputs are almost perfect in terms of responsiveness and I have enough accuracy to even drive with the remote! Both tapping and holding the remote translate very well to keyboard presses now.
- I plan on now removing the janky single tapping and ghost key flags I was using to get around the issues that were previously unsolved.


## Why Bother
- I play a lot of Beamng.Drive and there are only so many buttons on my Logitech G920 wheel that can be used to easily control the game. Reaching up to reach use the keyboard is not fun and really annoying, so I decided to figure out a way to add easily accessible keyboard controls without spending another dollar. It allows me to have a lot more fun for free! 