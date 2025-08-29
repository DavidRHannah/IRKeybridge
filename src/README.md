# IR Remote Controller

A small Python application to allow you to control your computer using any infrared remote control through an Arduino-based IR receiver.

## Features

- **Universal Remote Support**: Works with any IR remote control
- **Configurable Key Mappings**: Map IR codes to keyboard actions
- **Multiple Action Types**: Single keys, key combinations, sequences, and special actions
- **Profile Management**: Save and load different remote configurations
- **Ghost Key Mode**: Maintains application focus for games
- **Single Tap Mode**: Quick key press mode for rapid actions
- **Real-time Processing**: Low-latency IR code processing
- **Comprehensive Documentation**: Full API documentation with Sphinx

## Quick Start

### Hardware Setup

1. Connect an IR receiver to your Microcontroller board (Arduino, Elegoo, etc.)
2. Upload the provided firmware (`arduino_firmware/ir_to_serial.ino`)
3. Connect Arduino to your computer via USB

### Software Installation

1. Clone this repository
2. Install Python dependencies:
   ```bash
   pip install pyserial keyboard
   ```
3. Configure your serial port in `configs/settings.json`
4. Run the application:
   ```bash
   python main.py
   ```

## Documentation

### Building Documentation

The project includes comprehensive Sphinx documentation covering all modules and functions.

**Quick build:**
```bash
python build_docs.py --install --clean --open
```

**Manual build:**
```bash
cd docs
pip install -r requirements.txt
python -m sphinx -M html . _build
```

The generated documentation will be available at `docs/_build/html/index.html`.

### Documentation Features

- **Complete API Reference**: All classes, methods, and functions documented
- **Usage Examples**: Practical examples for each module
- **Configuration Guide**: Detailed configuration instructions
- **Architecture Overview**: System design and component interaction

## Configuration

### Application Settings

Edit `configs/settings.json`:

```json
{
    "serial_port": "COM5",
    "baud_rate": 9600,
    "timeout": 0.1,
    "ghost_key": "f10",
    "ghost_delay": 0.2,
    "repeat_threshold": 0.2
}
```

### Remote Profiles

Remote profiles are stored in `configs/` as JSON files. Each profile contains:

- Remote information (brand, model, description)
- IR code mappings to keyboard actions
- Action types (single, combo, sequence, special)

Example mapping:
```json
{
    "8": {
        "action_type": "combo",
        "keys": ["ctrl", "a"],
        "description": "Power button"
    }
}
```

## Action Types

- **SINGLE**: Press and hold a single key
- **COMBO**: Press multiple keys simultaneously (eg Ctrl+C)
- **SEQUENCE**: Press keys in sequence with delays
- **SPECIAL**: Special controller actions (toggle modes, stop)

## Special Features

### Ghost Key Mode
Sends an invisible key press to maintain application focus, useful for games that lose focus when other keys are pressed.

### Single Tap Mode
Converts all key actions to quick tap-and-release, useful for applications that don't need held keys.

## Development

### Adding New Features

1. Follow the existing code structure and documentation patterns
2. Add comprehensive docstrings to all functions and classes
3. Update the Sphinx documentation
4. Test with different remote controls

### Code Style

- Use type hints for all function parameters and return values
- Follow PEP 8 style guidelines
- Add comprehensive docstrings in Google/NumPy format
- Include usage examples in docstrings

## Troubleshooting

### Common Issues

1. **Serial Connection Failed**: Check COM port and Arduino connection
2. **No IR Codes Received**: Verify Arduino firmware and IR receiver wiring
3. **Keys Not Working**: Check remote profile mappings and key names

### Debug Mode

Enable debug logging by modifying the log level in the main controller.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive documentation for new features
4. Submit a pull request

## License

This project is open source. See LICENSE file for details.

## Hardware Requirements

- Arduino (Uno, Nano, or compatible)
- IR receiver module (e.g., TSOP4838)
- USB cable for Arduino connection
- Any IR remote control

## Software Requirements

- Python 3.8+
- pyserial library
- keyboard library
- Sphinx

## Support

For issues and questions:
1. Check the comprehensive documentation
2. Review existing configurations in `configs/`
3. Examine the Arduino firmware for hardware issues