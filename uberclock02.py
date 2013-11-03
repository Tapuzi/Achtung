'''
  __  __          _    _          _   _ ______ _______   ___   ___  __ ____  
 |  \/  |   /\   | |  | |   /\   | \ | |  ____|__   __| |__ \ / _ \/_ |___ \ 
 | \  / |  /  \  | |__| |  /  \  |  \| | |__     | |       ) | | | || | __) |
 | |\/| | / /\ \ |  __  | / /\ \ | . ` |  __|    | |      / /| | | || ||__ < 
 | |  | |/ ____ \| |  | |/ ____ \| |\  | |____   | |     / /_| |_| || |___) |
 |_|  |_/_/    \_\_|  |_/_/    \_\_| \_|______|  |_|    |____|\___/ |_|____/ 
 
 This file is a python code for communicating with MAHANET 2013 badge device.
 
 The badge is a relatively small device that is able to-
     - Measure acceleration, temprature and altitude
	 - Has 2-line 7-segment screen display, upper line is 4 digits\letters, lower line is 5
	 - Has backlight and a buzzer 
	 - Can communicate wirelessly with a usb AP(access-point) dongle
	 - It can do more but we wont tell you yet!!
	 - Each device has a unique id
 Every Mahanet member will receive the badge device together with the AP dongle at the beginning of the convention
 
 This code is given to you prior Mahanet so you have plenty of time to consider integrating with it and even start the integration.
 
 The code includes 2 classes that should be used - accessPointSocket and deviceConnection, a usage example can be found in the function xposeConnectionExample, which automatically runs if you execute this file (instead of just including it).
 Notice the usage example assumes a device id of '1337' and a connection port named 'COM13'.
 
 HAVE FUN!!
'''


import serial
import array
import time

def makeByteString(arr):
    return array.array('B', arr).tostring()

COMMAND_AP_STARTUP = makeByteString([0xFF, 0x07, 0x03])
COMMAND_AP_STOP = makeByteString([0xFF, 0x09, 0x03])
COMMAND_RECEIVE_DATA = makeByteString([0xFF, 0x33, 0x16, 0x03, 0x94, 0x34, 0x01, 0x07, 0xDA, 0x01, 0x17, 0x06, 0x1E, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
COMMAND_SEND_DATA_PREFIX = [0xFF, 0x31, 0x16]

DATA_PACKET_CONTENT_SIZE = 16
DATA_PACKET_ACK_BYTE = 6
DATA_PACKET_TYPE_DISCONNECT = 0xFF

MAX_SEQ_NUMBER = 255

XPOSE_STATE_FIELD_ACCELEROMETER = 0x1
XPOSE_STATE_FIELD_TEMPERATURE = 0x1 << 1
XPOSE_STATE_FIELD_ALTITUDE = 0x1 << 2
XPOSE_STATE_FIELD_LIGHT = 0x1 << 3
XPOSE_STATE_FIELD_BUZZ = 0x1 << 4

class accessPointSocket:
	# port - String representation of the relevant COM port (for windows check via device manager), e.g - 'COM11'
	def __init__(self, port):
		self.socket = serial.Serial(port, 115200, timeout=1)
		self.connections = {}
		self.pending = {}
		self.pending_device = 0
		self.incoming = {}
		
	def verifyAck(self, message):
		# Expect for an identical sized reply
		output = map(ord, self.socket.read(len(message)))
		
		# Make sure ack received
		if (DATA_PACKET_ACK_BYTE == output[1]):
			return True
		
		return False
	
	def verifyAckAndResponse(self, message):
		# Expect for an identical sized reply
		output = map(ord, self.socket.read(len(message)))
		
		# Make sure ack received
		if (DATA_PACKET_ACK_BYTE != output[1]):
			return None
		
		# Skip normal header
		return output[3:]
		
	def start(self):
		# Request for startup
		self.socket.write(COMMAND_AP_STARTUP)
		
		# Make sure ack received
		if (False == self.verifyAck(COMMAND_AP_STARTUP)):
			return False
		
		return True
		
	def stop(self):
		# Request for startup
		self.socket.write(COMMAND_AP_STOP)
		
		# Make sure ack received
		if (False == self.verifyAck(COMMAND_AP_STOP)):
			return False
		
		
		return True
	
	def parseDataPacket(self, packet):
		# Check data packet content length
		if ((DATA_PACKET_CONTENT_SIZE + 3) != len(packet)):
			return None
		
		# Sort content
		data = {}
		data['id'] = (packet[1] << 8) + packet[2]
		data['seq'] = packet[3]
		data['content'] = packet[4:]
		data['type'] = packet[4]
		
		return data
		
	def receiveDataPacket(self):
		# We request from the ap the last data packet it received 
		self.socket.write(COMMAND_RECEIVE_DATA)
		response = self.verifyAckAndResponse(COMMAND_RECEIVE_DATA)

		# If no data packet received
		if (None == response):
			return None
		
		#print response
		# Parse data packet content
		data = self.parseDataPacket(response)
		
		# Notice data might be None
		return data
	
	def sendDataPacket(self, data):
		# Make sure valid content size
		if (len(data['content']) > DATA_PACKET_CONTENT_SIZE):
			return False
		
		# Pad data content
		data['content'] += [0x00] * (DATA_PACKET_CONTENT_SIZE - len(data['content']))
		
		# Build messge: device_id | msg seq No | content
		msg = list(COMMAND_SEND_DATA_PREFIX)
		msg += [(data['id'] & 0xFF00) >> 8,
				(data['id'] & 0xFF),
				(data['seq'])] + data['content']
		
		print "sending " + str(msg)
		# Ask ap to send the packet
		self.socket.write(makeByteString(msg))		
		return self.verifyAck(makeByteString(msg))
		
	def doReceive(self):
		# Check ap for received data
		data = self.receiveDataPacket()
		#print "got" + str(data)
		# If data is from a connected device
		if (self.connections.has_key(data['id'])):
			# If we did not get that message yet
			if (self.connections[data['id']] < data['seq']):
				# If end device requested disconnection
				if (DATA_PACKET_TYPE_DISCONNECT == data['type']):
					self.connections.pop(data['id'])
				else:
					self.connections[data['id']] = data['seq']
				
				# Add the message to the incoming data list
				if (None == self.incoming[data['id']]):
					self.incoming[data['id']] = [data]
				else:
					self.incoming[data['id']] += [data]
					
				# If sequence is about to wrap around
				if (self.connections.has_key(data['id'])) and (self.connections[data['id']] > (MAX_SEQ_NUMBER-10)):
					self.connections[data['id']] = 0
					
				return True
				
		# If data is not from a connected device
		else:
			# If it is a connection request from a device
			if (0 == data['id']):
				print "Received new connection request"
				# Answer that we agree to add a new connection only from the pending id
				connectRequest = {}
				connectRequest['id'] = self.pending_device
				connectRequest['seq'] = 1
				connectRequest['content'] = [0x00]
				
				if (True == self.sendDataPacket(connectRequest)):
					# Remember we are in pending state
					self.pending[connectRequest['id']] = 0
			
			# If it a a connection sucessfull from a pending device
			elif (self.pending.has_key(data['id'])):
				# Add it to connections list, delete from pending
				self.connections[data['id']] = data['seq']
				self.pending.pop(data['id'])
				self.incoming[data['id']] = [data]
				
				return True
				
		return None
		
	# device_id - 4 hex digits in string representation
	def connect(self, device_id):
		# At a certain time there can be only 1 pending device for connection
		self.pending_device = int(device_id, 16)
	
	# device_id - 4 hex digits in string representation
	def isConnected(self, device_id):
		return self.connections.has_key(int(device_id, 16))
	
	# device_id - 4 hex digits in string representation
	def pullMessages(self, device_id):
		# If we have messages from the device id
		if (self.incoming.has_key(int(device_id, 16))):
			deviceMessages = self.incoming[int(device_id, 16)]
			self.incoming[int(device_id, 16)] = None
			
			# If those were the last messages of this device and it disconnected
			if (not self.connections.has_key(int(device_id, 16))):
				self.incoming.pop(int(device_id, 16))

			return deviceMessages
		
		return None


class deviceConnection:
	# device_id - 4 characters in string representation
	def __init__(self, access_point_socket, device_id):
		self.device_id = device_id
		self.ap_socket = access_point_socket
		
		# Initial seq number
		self.seq = 2
		
	# This function is blocking
	def connect_to_device(self):
		# Inform that a connection to this device is expected
		self.ap_socket.connect(self.device_id)
		
		# Wait for the device to connect
		while (False == self.ap_socket.isConnected(self.device_id)):
			self.ap_socket.doReceive()

	def sync_settings(self, accelerometer=True, altimeter=False, temperature=False, backlight=False, upper_text='    ', lower_text='     ', buzz=False, rate=100):
		# First convert state requests to bitfield
		state = 0
		
		if (accelerometer): 
			state |= XPOSE_STATE_FIELD_ACCELEROMETER
			
		if (altimeter): 
			state |= XPOSE_STATE_FIELD_ALTITUDE
			
		if (temperature): 
			state |= XPOSE_STATE_FIELD_TEMPERATURE
			
		if (backlight): 
			state |= XPOSE_STATE_FIELD_LIGHT
			
		if (buzz): 
			state |= XPOSE_STATE_FIELD_BUZZ
		

		# Validate texts
		upper_text = upper_text.upper()
		lower_text = lower_text.upper()
		
		if (4 != len(upper_text)):
			upper_text = '    '
			
		if (5 != len(lower_text)):
			lower_text = '     '
		
		# Serialize rate
		rate_high = (rate & 0xFF00) >> 8
		rate_low = rate & 0xFF
		
		# Prepare packet
		send_data = {}
		send_data['seq'] = self.seq
		self.seq += 1
		send_data['id'] = int(self.device_id, 16)
		send_data['content'] = [state, rate_high, rate_low] + map(ord,lower_text) + map(ord,upper_text)
		
		# Send packet
		if (False == self.ap_socket.sendDataPacket(send_data)):
			return False
		
		return True

	def is_device_connected(self):
		return self.ap_socket.isConnected(self.device_id)
	
	def parse_messages(self, messages):
		if (None == messages):
			return None
		
		parsed_messages = []
		
		for single_message in messages:
			parsed_single_message = {}
			# Parse te message
			parsed_single_message['accel_x'] = single_message['content'][1]
			parsed_single_message['accel_y'] = single_message['content'][2]
			parsed_single_message['accel_z'] = single_message['content'][3]
			parsed_single_message['temp'] = single_message['content'][4] + (single_message['content'][5] << 8)
			parsed_single_message['alt'] = single_message['content'][6] + (single_message['content'][7] << 8)
			parsed_single_message['buttons'] = single_message['content'][9]
			# Append it
			parsed_messages.append(dict(parsed_single_message))
		
		return parsed_messages
		
	def receive(self):
		# Receive all
		self.ap_socket.doReceive()
		# Look for messages from our device
		messages = self.ap_socket.pullMessages(self.device_id)
		
		# Parse those messages and return them
		messages = self.parse_messages(messages)
		return messages


# deviceId - A 2 byte hex number in string representation (e.g '1337')
# comPort - A string representation of comport identifier (e.g 'COM10')
def xposeConnectionExample(deviceId, comPort):
	# Connect to the ap
	ap_socket = accessPointSocket(comPort)
	# Turn on ap
	ap_socket.start()
	
	# Create a device connection object and link it to ap socket
	device_connection = deviceConnection(ap_socket, deviceId)
	
	print "waiting for " + deviceId
	device_connection.connect_to_device()
	print "%s connected!" % deviceId

	start_time = time.time()
	
	first_trigger = False
	second_trigger = False
	third_trigger = False
	counter = 1
	# As long as the device is connected
	while (device_connection.is_device_connected()):
		# Look for messages from that device
		messages = device_connection.receive()

		if (None != messages):
			# Display them
			print messages
		
		current_time = time.time() - start_time
		
		'''
		# After 4 seconds activate 1st trigger which turns on backlight and writes "GLOW"
		if ((current_time > 4) and not first_trigger):
			first_trigger = True
			device_connection.sync_settings(accelerometer=False, altimeter=False, temperature=False, upper_text="GLOW")
		'''
		
		# After 4 seconds activate 1st trigger which turns on backlight and writes "GLOW"
		if ((current_time > 4) and not first_trigger):
			first_trigger = True
			device_connection.sync_settings(backlight=True, upper_text="GLOW")

		# After 7 seconds activate 2nd trigger which turns off backlight, turns on temprature and altimeter readings
		if ((current_time > 11) and not second_trigger):
			second_trigger = True
			device_connection.sync_settings(backlight=False, temperature=True, altimeter=True, upper_text=" HEY", buzz=True)

		# After 11 seconds activate 2nd trigger which writes "HO" and raises the rate
		if ((current_time > 15) and not third_trigger):
			third_trigger = True
			device_connection.sync_settings(lower_text="   HO", rate=10)
		
		'''
		if (current_time > (counter * 2)) and (current_time > 20):
			counter += 1
			device_connection.sync_settings(rate=10, buzz=True)
		'''
		
	print "device %s disconnected!" % deviceId

	# Turn off ap
	ap_socket.stop()

if ('__main__' == __name__):
	# For windows systems use 'COM_' , for linux use '/dev/ttyACM0'
	xposeConnectionExample('1337', 'COM10')
