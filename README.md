# 🎮 IRKeybridge

**Transform any IR remote into a wireless keyboard controller**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Coverage](https://img.shields.io/badge/coverage-70%25-brightgreen.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey.svg)

---

## 🚀 What is IRKeybridge?

IRKeybridge lets you use **any IR remote control** as a wireless keyboard for your PC. Perfect for gaming, media control, or any application where you need quick access to keyboard shortcuts without reaching for your keyboard.

Created to add extra controls for BeamNG.Drive racing without spending a single dollar more!

### ✨ Key Features

- 🎯 **Universal Remote Support** - Works with TV remotes, cable boxes, air conditioners - anything with IR
- ⚡ **Low Latency** - Responsive enough for real-time gaming
<!-- - 🎮 **Gaming Optimized** - Ghost key mode maintains game focus -->
- 🖥️ **Dual Interface** - Beautiful GUI + powerful CLI
<!-- - 📝 **Smart Profiles** - Save configurations for different remotes/games -->
- 🔧 **Easy Setup** - Learn IR codes directly from your remote

---

## 🛠️ Quick Setup

### Hardware Requirements
- Arduino Uno/Nano (or compatible)
- IR Receiver (TSOP4838, VS1838B, or similar) 
- Any IR remote control
- USB cable

### Software Installation
```bash
git clone https://github.com/yourusername/IRKeybridge.git
cd IRKeybridge
pip install -r requirements.txt
```

### Flash Arduino Firmware
1. Upload the provided Arduino sketch to your microcontroller
2. Connect IR receiver to your Arduino
3. Note the COM port in Device Manager

### Run the Application
```bash
# GUI Mode (Recommended for first-time setup)
python run_app.py --gui

# CLI Mode
python run_app.py --cli

# Quick start with interactive setup
python run_app.py
```

---

## 🎮 Usage Examples

### Gaming Setup
Map your TV remote buttons to game controls:
- **Volume Up/Down** → Gear shifting
- **Channel Up/Down** → Camera angles  
- **Play/Pause** → Handbrake
- **Arrow Keys** → Menu navigation

### Media Control
- **Power** → Play/Pause media
- **Volume** → System volume
- **Numbers** → Hotkeys for applications

### Custom Workflows
Create button combinations and sequences for complex actions.

---

## 📱 Interface Options

### 🖼️ GUI Mode
- **Visual IR Learning** - Point remote, press button, assign action
- **Profile Manager** - Create and switch between remote configurations  
- **Serial Monitor** - Real-time Arduino communication
- **System Settings** - Configure all options in one place

### 💻 CLI Mode  
```bash
# List available profiles
python run_app.py --cli --list-profiles

# Load specific profile
python run_app.py --cli --profile my_remote.json

# Enable special modes
python run_app.py --cli --enable-ghost --enable-tap

# Create executable
pyinstaller --onefile --noconsole run_app.py
```

---

## 📋 Configuration

### Profile Structure
```json
{
    "name": "Gaming Remote",
    "brand": "Samsung TV",
    "mappings": {
        "FF": {
            "action_type": "single",
            "keys": "space",
            "description": "Jump"
        },
        "AA": {
            "action_type": "combo", 
            "keys": ["ctrl", "shift", "r"],
            "description": "Quick Restart"
        }
    }
}
```

### Action Types
- **Single Key** - `space`, `enter`, `f1`
- **Key Combinations** - `["ctrl", "c"]`, `["alt", "tab"]`
- **Key Sequences** - Multiple actions in order
- **Special Actions** - System commands, macros

---

## 🧪 Testing & Development

### Run Tests
```bash
# Full test suite
python run_app.py --test

# Coverage report
python run_app.py --coverage

# Debug mode
python run_app.py --cli --debug --verbose
```

### Code Formatting
```bash
black src/ tests/
```

**Test Coverage:** >70% with comprehensive unit, integration, and GUI tests.

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| **No Serial Connection** | Check COM port, try different USB cable |
| **IR Codes Not Received** | Verify firmware upload, check IR receiver wiring |
| **Keys Not Working** | Confirm profile mappings, try Ghost Key mode |
| **GUI Won't Start** | Install PyQt5, check Python 3.8+ |

**Debug Mode:** `python run_app.py --cli --debug` for detailed logging.

---

## 🎯 Why IRKeybridge?

✅ **Free Solution** - No expensive gaming keypads needed  
✅ **Universal Compatibility** - Works with any IR remote you have  
✅ **Gaming Performance** - Low latency, responsive controls  
✅ **Customizable** - Map any button to any keyboard action  
✅ **Production Ready** - Comprehensive error handling and logging  
✅ **Open Source** - Modify and extend as needed  

---

## 📦 Create Standalone Executable

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name="IRKeybridge" run_app.py
```

Stop the background service via Task Manager or your configured stop button.

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b new-feature`)
3. Add tests for new functionality
4. Update documentation
5. Submit pull request

---

## 📄 License

This project is open source under the MIT License. See `LICENSE` file for details.

---

## 🙏 Acknowledgments

Created out of the need for extra accessible controls in BeamNG.Drive racing.

**Happy Racing! 🏎️**