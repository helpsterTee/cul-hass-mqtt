# cul-hass-mqtt
A lightweight Python3 parser for publishing FS20 messages from a serial CUL device to home-assistant using a MQTT server.

Notes: This is tested on Ubuntu Linux, but should work on a RaspberryPi or similar

## Requirements
* A compatible CUL device. I'm using a self-built Arduino nano v3 CUL: https://wiki.fhem.de/wiki/Selbstbau_CUL#Software (German language)
* PySerial and Paho-MQTT libraries for Python3

## Installation
1. Set up Python3
2. Clone or download this repository
3. `pip3 install pyserial paho-mqtt`
4. Open cul.py and adjust config values accordingly (especially the serial port)
5. Check you have full access to the serial port
6. Enable home-assistant MQTT plugin in configuration.yml:
```YAML
mqtt:
    discovery: true
    discovery_prefix: homeassistant
```
7. `python3 cul.py` and cross your fingers

## Known bugs
* When starting the application, home-assistant will autodiscover a new device. It will create duplicate devices on every new restart of cul-hass-mqtt. This is a known bug with the MQTT service, so just restart home-assistant to remove duplicates.
* The only supported types at the moment are ON / OFF binary_switches. Feel free to create a pull request for extensions!

## Contributing
* Create a pull request with your code.

## LICENSE
MIT, see LICENSE
