# ir-to-serial-to-keyboard

## My setup
1. Elegoo Uno R3
1. IR Receiver
1. Vizio Remote

## High-Level Overview
The Uno R3 microcontroller is for sending the IR Receiver's digital output from the input of an IR remote (i.e. Vizio remote) to the Serial Output by the virtual COM port (i.e. COM5) so that the data from the receiver can be processed by a python script. Since the Elegoo Uno R3 is not intended to be a HID device ([although it can be made to be](https://github.com/Franzerz/uno-HID-keyboard)), the python script should be running when when using the IR remote.

## Steps For Implementing Yourself
1. Obtain cheap microcontroller and IR receiver
1. Find old Vizio IR remote
1. Flash given firmware onto microcontroller
1. Setup keybinds in game and/or script
1. Run python script

You *should* now be able to use your remote! Hopefully...

## Changes
The current implementation uses the pyatuogui library for making key presses however, it does not working for using hotkeys as well as other libraries like keyboard.

## Why Bother
I play a lot of Beamng.Drive and there are only so many buttons on my Logitech G920 whell that can be used to easily control the game. Reaching up to reach use the keyboard is not fun and really annoying, so I decided to figure out a way to add easily accessible keyboard controls without spending another dollar. It allows me to have a lot more fun for free! 