IR Remote Remote To Keyboard
My setup
Elegoo Uno R3
IR Receiver
IR Based Remote (i.e. Vizio)
High-Level Overview
The Uno R3 microcontroller is for sending the IR Receiver's digital output from the input of an IR remote (i.e. Vizio remote) to the Serial Output by the virtual COM port (i.e. COM5) so that the data from the receiver can be processed by a python script. Since the Elegoo Uno R3 is not intended to be a HID device (although it can be made to be), the python script should be running when when using the IR remote.

Steps For Implementing Yourself
Obtain cheap microcontroller and IR receiver
Find old Vizio IR remote
Flash given firmware onto a microcontroller
Setup keybinds in game and/or script
Run python script
Note
You can generate an executable for yourself to run in the background so you don't have to worry about keeping the python script running by using pyinstaller:
pyinstaller --onefile --noconsole --uac-admin=False ir_control.py
You can end the exe by ending the process via Task Manager or by hitting the STOP (x30) key or whatever you program it to be.
You should now be able to use your remote! Hopefully...

Changes
The current implementation uses the python keyboard library for its precise customization of keyboard commands/inputs.
The inputs are almost perfect in terms of responsiveness and I have enough accuracy to even drive with the remote! Both tapping and holding the remote translate very well to keyboard presses now.
I plan on now removing the janky single tapping and ghost key flags I was using to get around the issues that were previously unsolved.
Why Bother
I play a lot of Beamng.Drive and there are only so many buttons on my Logitech G920 wheel that can be used to easily control the game. Reaching up to reach use the keyboard is not fun and really annoying, so I decided to figure out a way to add easily accessible keyboard controls without spending another dollar. It allows me to have a lot more fun for free!

```bash
python run_app.py --gui
python run_app.py --cli
python run_app.py
```

## Features

### Core Features
- **Universal Remote Support**: Works with any IR remote control
- **Multiple Action Types**: Single keys, combinations, sequences, and special actions
- **Profile Management**: Save and load different remote configurations
- **Real-time Processing**: Low-latency IR code processing
- **Production Ready**: Comprehensive error handling and logging

### GUI Features
- **Visual Configuration**: Easy-to-use graphical interface
- **IR Code Learning**: Learn codes directly from your remote
- **Profile Editor**: Create and modify remote profiles
- **Serial Monitor**: Real-time Arduino communication monitoring
- **System Configuration**: Manage all settings from one place

### CLI Features
- **Command-line Interface**: Full CLI with comprehensive options
- **Interactive Mode**: Guided profile selection
- **Batch Operations**: Script-friendly commands
- **Status Monitoring**: Real-time system status

### Special Modes
- **Ghost Key Mode**: Maintains application focus for games
- **Single Tap Mode**: Quick key press mode for rapid actions
- **Debug Mode**: Detailed logging for troubleshooting

The GUI provides:
- **System Config**: Configure Arduino connection and settings
- **Remote Config**: Learn IR codes and create button mappings
- **Profile Management**: Save and load different configurations

### CLI Mode

Use the command-line interface for advanced control:

```bash
python run_app.py --cli --list-profiles
python run_app.py --cli --profile my_remote.json
python run_app.py --cli --create-default
python run_app.py --cli --status
python run_app.py --cli --enable-ghost --enable-tap
```

### Configuration

#### Remote Profiles

Profiles are stored in `config/profiles/` as JSON files:

```json
{
    "name": "My Remote",
    "brand": "Samsung",
    "model": "TV Remote",
    "mappings": {
        "FF": {
            "action_type": "single",
            "keys": "space",
            "description": "Play/Pause"
        },
        "AA": {
            "action_type": "combo",
            "keys": ["ctrl", "c"],
            "description": "Copy"
        }
    }
}
```

## Testing

This application includes comprehensive testing with >70% code coverage:

```bash
python run_app.py --test
python run_app.py --coverage
```

### Test Coverage

The test suite covers:
- **Unit Tests**: All core modules (config, IR receiver, key mapper, controller)
- **Integration Tests**: End-to-end application flow
- **GUI Tests**: User interface components (mocked)
- **CLI Tests**: Command-line interface functionality
- **Error Handling**: Comprehensive error scenarios

## Executables
### Windows Executable

Create a standalone executable:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name="IR-Remote-Controller" run_app.py
```

### Service Installation

For background operation, create a Windows service or Linux daemon using the CLI mode.

## Development

### Code Formatting

```bash
black src/ tests/
```

## Troubleshooting

### Common Issues

1. **Serial Connection Failed**
   - Check COM port in Device Manager
   - Verify microcontroller is connected and recognized
   - Try different USB cable/port

2. **No IR Codes Received**
   - Verify microcontroller firmware is uploaded correctly
   - Check IR receiver wiring and power
   - Test with known working remote

3. **Keys Not Working**
   - Verify profile mappings are correct
   - Check if target application has focus
   - Try enabling Ghost Key mode for games

4. **GUI Won't Start**
   - Install PyQt5: `pip install PyQt5`
   - Check Python version (3.8+ required)
   - Try CLI mode as fallback

### Debug Mode

Enable extensive logging:

```bash
python run_app.py --cli --debug --verbose
```

### Getting Help

1. Check the comprehensive documentation in `docs/`
2. Review existing configurations in `config/profiles/`
3. Examine Microcontroller firmware for hardware issues
4. Run the test suite to verify installation

## License

This project is open source. See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Update documentation
5. Submit a pull request

## Hardware Requirements

- **Arduino**: Uno, Nano, or compatible microcontroller
- **IR Receiver**: TSOP4838, VS1838B, or similar
- **Remote**: Most infrared remote control
- **Connection**: USB cable for microcontroller board

## Software Requirements

- **Python**: 3.8 or higher
- **Core Dependencies**: pyserial, keyboard
- **GUI Dependencies**: PyQt5 (optional)
- **Development**: pytest, coverage tools

---