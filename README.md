# PyANTDisplay - ANT+ Device Data Display

A Python application for reading data from ANT+ devices using an ANT+ USB stick. This project specifically supports heart rate monitors and bike sensors (speed/cadence), with device discovery and configuration capabilities.

[![CI](https://github.com/Velotales/pyAntDisplay/workflows/CI/badge.svg)](https://github.com/Velotales/pyAntDisplay/actions)
[![Coverage](https://codecov.io/gh/Velotales/pyAntDisplay/branch/main/graph/badge.svg)](https://codecov.io/gh/Velotales/pyAntDisplay)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Platform Support

**⚠️ Linux Only**: This application is currently tested and supported only on Ubuntu/Debian systems. While the code may work on other Linux distributions, macOS, or Windows, it has not been tested on these platforms and USB device access may require additional configuration.

## Features

- **Device Discovery**: Scan for available ANT+ devices and save them to a configuration file
- **Heart Rate Monitoring**: Connect to ANT+ heart rate monitors and display real-time heart rate data
- **Bike Sensor Data**: Read speed, cadence, and distance data from ANT+ bike sensors
- **Live Dashboard**: Real-time curses-based dashboard with multi-user support
- **MQTT Integration**: Home Assistant compatible MQTT publishing for IoT automation
- **Service Mode**: Run as systemd service for continuous background monitoring
- **Configuration Management**: Easy device setup and configuration through interactive menus
- **Real-time Display**: Live data display with color-coded status indicators

## Requirements

- ANT+ USB stick (compatible with libusb)
- Python 3.8+
- ANT+ devices (heart rate monitor, bike speed/cadence sensor)

### System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3-venv python3-pip libusb-1.0-0-dev
```

**CentOS/RHEL:**
```bash
sudo yum install python3-venv python3-pip libusb1-devel
```

**Fedora:**
```bash
sudo dnf install python3-venv python3-pip libusb1-devel
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip libusb
```

## Installation

1. Clone or download this project to your local machine:
```bash
git clone https://github.com/Velotales/pyAntDisplay.git
cd pyAntDisplay
```

2. Set up the virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

This will create a virtual environment in the `.venv/` directory and install all required packages. Runtime data (discovered devices, logs) will be stored in the `data/` directory.

3. Make sure your ANT+ USB stick is connected and accessible. You may need to set up udev rules for USB access:

```bash
# Create udev rule for ANT+ stick (adjust vendor/product ID as needed)
sudo nano /etc/udev/rules.d/99-ant-stick.rules
```

Add this line (adjust the idVendor and idProduct for your device):
```
SUBSYSTEM=="usb", ATTRS{idVendor}=="0fcf", ATTRS{idProduct}=="1008", MODE="0666"
```

Then reload udev rules:
```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
```

## Usage

### Application Modes

PyANTDisplay supports five different modes via the unified entry point:

```bash
# Activate the virtual environment
source .venv/bin/activate
source .venv/bin/activate

# Windows  
# .venv\Scripts\activate

# Interactive menu with GUI
python -m pyantdisplay --mode menu

# Scan for ANT+ devices  
python -m pyantdisplay --mode scan --app-config config/config.yaml

# List discovered devices
python -m pyantdisplay --mode list --app-config config/config.yaml

# Live dashboard monitor
python -m pyantdisplay --mode monitor --config config/sensor_map.yaml

# MQTT publisher for Home Assistant
python -m pyantdisplay --mode mqtt --config config/sensor_map.yaml --app-config config/config.yaml
```

### Getting Started

1. **First Run**: Start with the interactive menu
   ```bash
   python -m pyantdisplay --mode menu --app-config config/config.yaml
   ```

2. **Scan for Devices**: Use option 1 to discover your ANT+ devices (30 second scan)

3. **Configure Mapping**: Edit `config/sensor_map.yaml` with discovered device IDs

4. **Start Monitoring**: Choose live dashboard or MQTT publishing mode

## Configuration

### Main Configuration (`config/config.yaml`)

```yaml
devices:
  heart_rate:
    device_id: null  # Set after device discovery
    device_type: 120  # ANT+ Heart Rate Monitor
    enabled: true
  bike_data:
    device_id: null  # Set after device discovery  
    device_type: 121  # ANT+ Speed and Cadence
    enabled: true

ant_network:
  key: [0xB9, 0xA5, 0x21, 0xFB, 0xBD, 0x72, 0xC3, 0x45]  # ANT+ network key
  frequency: 57

app:
  scan_timeout: 30  # Device scan timeout in seconds
  data_display_interval: 1  # Data refresh interval in seconds
  found_devices_file: "found_devices.json"
  backend: "openant"  # or "python-ant"

mqtt:
  host: "localhost"
  port: 1883
  username: null
  password: null
  base_topic: "pyantdisplay"
  qos: 1
  retain: true
  stale_secs: 10
  client_id: "pyantdisplay-mqtt"
  discovery: true
  discovery_prefix: "homeassistant"
```

### Sensor Mapping (`config/sensor_map.yaml`)

```yaml
sensor_map:
  users:
    - name: "John"
      hr_device_ids: [25377, 38847]  # Multiple HR monitors can be assigned to same user
      speed_device_id: null
      cadence_device_id: null
    - name: "Sarah"  
      hr_device_ids: [42103]         # Single HR monitor
      speed_device_id: 12345
      cadence_device_id: null
```

**Multiple Heart Rate Devices per User**: You can assign multiple heart rate monitors to a single user by listing their device IDs in the `hr_device_ids` array. The system will automatically use whichever device is currently active/transmitting. This is useful when users have multiple HR monitors (chest strap, watch, etc.) and want seamless switching between them.

### Local Config Overrides (`config/config_local.yaml`)

Create this file for machine-specific settings (ignored by Git):

```bash
# Copy the base config as starting point
cp config/config.yaml config/config_local.yaml
# Edit with your actual settings
nano config/config_local.yaml
```

Example local overrides:
```yaml
mqtt:
  host: "your-mqtt-broker.local"
  port: 1883
  username: "homeassistant"
  password: "secret"
  tls: false

devices:
  heart_rate:
    device_id: 25377  # Your discovered device ID
```

Pass local config via `--local-config config/config_local.yaml` to override base settings.

## Supported Devices

- **Heart Rate Monitors** (Device Type 120)
  - Standard ANT+ heart rate monitors
  - Displays BPM and R-R intervals

- **Bike Sensors** (Device Type 121, 122, 123)
  - Speed and cadence sensors
  - Individual speed or cadence sensors
  - Displays speed (km/h), cadence (RPM), and trip distance

## Service Deployment

For continuous monitoring and MQTT publishing, PyANTDisplay can run as a systemd service. This is ideal for home automation setups where you want ANT+ devices to continuously publish data to your MQTT broker.

### Service Installation

```bash
# Copy and customize the service file
sudo cp pyantdisplay.service /etc/systemd/system/
sudo nano /etc/systemd/system/pyantdisplay.service

# Update these paths in the service file:
# - User and Group (e.g., pi, your-user)
# - WorkingDirectory (/path/to/your/pyAntDisplay)
# - ExecStart (/path/to/your/pyAntDisplay/.venv/bin/python)
# - ReadWritePaths (/path/to/your/pyAntDisplay)

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable pyantdisplay.service
sudo systemctl start pyantdisplay.service
```

### Service Management

```bash
# Check service status
sudo systemctl status pyantdisplay.service

# View live logs
sudo journalctl -u pyantdisplay.service -f

# Restart service (e.g., after config changes)
sudo systemctl restart pyantdisplay.service
```

### Home Assistant Integration

When running as a service, the MQTT mode automatically:

- **Publishes device discovery** messages for Home Assistant
- **Creates sensor entities** for each mapped ANT+ device
- **Updates sensor values** in real-time
- **Tracks device availability** (online/offline status)
- **Maintains persistent connections** to MQTT broker

Example Home Assistant entities created:
- `sensor.john_heart_rate` - Heart rate in BPM
- `sensor.john_speed` - Speed in km/h  
- `sensor.john_cadence` - Cadence in RPM
- `binary_sensor.john_hr_monitor_available` - Device status

## Data Display

The real-time display shows:

### Heart Rate Monitor
- Current heart rate in BPM
- R-R interval data for heart rate variability analysis
- Connection status

### Bike Sensor
- Current speed in km/h
- Current cadence in RPM  
- Trip distance in km
- Connection status

## Troubleshooting

### Device Not Found
- Ensure ANT+ devices are active and transmitting
- Check that the ANT+ USB stick is properly connected
- Try scanning multiple times as devices may not always be detected immediately
- Verify device compatibility with ANT+ protocol

### Permission Issues (Linux)
- Set up udev rules as described in the installation section
- Run with sudo if necessary (not recommended for regular use)
- Check that your user is in the appropriate groups (dialout, plugdev)

### Connection Problems
- Verify device IDs are correctly configured
- Check that devices haven't changed IDs (some devices cycle IDs)
- Ensure devices are within range and have battery power

### Data Issues
- Check that devices are actively transmitting (moving for bike sensors)
- Verify wheel circumference setting for accurate speed calculations
- Ensure devices are properly paired/configured

## Technical Details

### ANT+ Protocol
- Uses standard ANT+ network key
- Operates on 2.4 GHz frequency
- Device-specific message parsing for heart rate and bike sensors

### Data Processing
- Heart rate: Extracts BPM and R-R intervals from ANT+ HR messages
- Bike sensors: Calculates speed and cadence from revolution counts and timing
- Distance calculation: Uses configurable wheel circumference

### Architecture
- Modular design with separate classes for each device type
- Event-driven data processing with callbacks
- Thread-safe data updates and display

## Contributing

Feel free to contribute improvements, bug fixes, or support for additional ANT+ device types.

## License

This project is provided as-is for educational and personal use.