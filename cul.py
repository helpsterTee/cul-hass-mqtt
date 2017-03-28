import sys
import serial
import serial.threaded
import io
import time
import json
import paho.mqtt.client as mqtt

#### CONFIG HERE ####

# Serial Device
DEVICE = '/dev/ttyUSB0'
BAUDRATE = 38400
PARITY = 'N'
RTSCTS = False
XONXOFF = False

# Serial Operations
TIMEOUT = 1 #s
INIT_SLEEP_TIME = 3 # how many seconds do we wait for the serial device to accept commands?
LOOP_SLEEP_TIME = 1 # read serial data every x seconds to prevent high CPU usage

# MQTT Config
MQTT_SERVER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_CONTEXT = "homeassistant/binary_sensor/" # modify this for other uses, currently this has only binary sensors supported

# Translate device IDs to common names
# If you don't have a device ID in here, it will be ignored!
DEVICE_NAMES = {
	"1111": "doorbell"
}

# Translate device IDs to device_class
DEVICE_CLASS = {
	"1111": "motion"
}

### END OF CONFIG ###


######## Don't modify below here unless you know what you're doing ###########
STATE_CODES = {
	"1111": "OFF",
	"1212": "ON",
}

def hexToElv(string):
	retStr = ""
	for i in range(0,len(string),1):
		substr = string[i]
		# Convert strange ELV notation on base 4 to base 10
		hexint = int(substr,16)
		l_int = hexint % 4 + 1 # 1 to 4 instead of 0 to 3
		r_int = int(hexint / 4)
		h_int = r_int % 4 + 1
		retStr += str(h_int) + str(l_int)
	return retStr

# last two bytes are the RSSI value in dBm
def getRSSI(string):
	return int(string,16)-256-74

# first four bytes are the house code
def getHauscode(string):
	return string[0:8]

# next two bytes are the device address
def getDevicecode(string):
	return string[8:12]

def getCommonName(string):
	if string in DEVICE_NAMES:
		return DEVICE_NAMES[string]
	else:
		return None

# next two bytes are state
def getState(string):
	return STATE_CODES[string[12:16]]


ser = serial.serial_for_url(DEVICE, do_not_open=True, timeout=TIMEOUT)
ser.baudrate = BAUDRATE
ser.parity = PARITY
ser.rtscts = RTSCTS
ser.xonxoff = XONXOFF

try:
        ser.open()
except serial.SerialException as e:
        sys.stderr.write('Could not open serial port {}: {}\n'.format(ser.name, e))
        sys.exit(1)

time.sleep(INIT_SLEEP_TIME) # we have to wait for init
ser.write(b"X21\r\n") # set mode to receive known good packets with RSSI attached

# Initialize the MQTT connection
def mqtt_onconnect(client, userdata, flags, rc):
	if rc == 0:
		print("Connected to MQTT")
		client.subscribe(MQTT_CONTEXT+"#")
		for key in DEVICE_NAMES:
			configjson = {
				"name": DEVICE_NAMES[key],
				"device_class": DEVICE_CLASS[key]
			}
			client.publish(MQTT_CONTEXT+DEVICE_NAMES[key]+"/config", None, 1, True) # clear old config messages to prevent duplicate devices
			client.publish(MQTT_CONTEXT+DEVICE_NAMES[key]+"/config", json.dumps(configjson))
	else:
		print("There was an error connecting to the MQTT server")

def mqtt_onmessage(client, userdata, msg):
	print(msg.topic + " " + str(msg.payload))

client = mqtt.Client()
client.on_connect = mqtt_onconnect
client.on_message = mqtt_onmessage

client.connect(MQTT_SERVER, MQTT_PORT, 60)
client.loop_start()

while(True): # Loopy McLoopface
	time.sleep(LOOP_SLEEP_TIME) # Sleep every so often to diminish CPU usage
	if (ser.inWaiting()>0): # Only iterate on data, if there is any
		data = ser.read(ser.inWaiting())
		data_str = data.decode('ascii')
		parseString = hexToElv(data_str[1:len(data_str)-4])

		housecode = getHauscode(parseString)
		devicecode = getDevicecode(parseString)
		commonName = getCommonName(devicecode)

		if commonName is None:
			continue;

		state = getState(parseString)
		rssi = getRSSI(data_str[9:11])
		content = {
			"housecode": housecode,
			"deviceaddress": devicecode,
			"commonname": commonName,
			"state": state,
			"rssi": str(rssi)
		}
		print(json.dumps(content))

		print("Sending state change for <"+commonName+"> to ["+state+"]")
		client.publish(MQTT_CONTEXT+commonName+"/state", state)


#ser.close() #We're not going to end up here anyways
