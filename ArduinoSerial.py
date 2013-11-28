import serial
import time
class ArduinoController(object):
	'''
	self class controls each individual field unit by a unique id.
	At runtime, we should make a certain number copies of self class
	foreach field unit we want to play with.
	'''
	def __init__(self, commander, uid):
		# The serial commander
		self.commander = commander

		# Unique uid for each field unit
		self.uid = uid

	def start(self, speed, delay=0):
		'''
		Starts the arduino field unit, there is a delay option for countdown(?)
		'''
		self.sendCommand("start", speed)

	def stop(self, delay=0):
		'''
		Stops the arduino field unit, there is a delay option for countdown(?)
		'''
		time.sleep(delay)
		self.sendCommand("stop", 0)

	def setSpeedLeft(self, speed):
		'''
		Sets the speed of the left wheel
		'''
		self.sendCommand("setLeft", speed)

	def setSpeedRight(self, speed):
		'''
		Sets the speed of the left wheel
		'''
		self.sendCommand("setRight", speed)

	def move(self, direction):
		'''
		Move the field unit to a certain direction
		TODO: consult with the rest of the team on the protocol
		'''
		self.sendCommand("move", direction)

	def sendCommand(self, key, value):
		'''
		A general function that sends the action via the commander
		The command must be a '\n' terminated.
		'''
		command = "uid=%s;key=%s;value=%s;\n" % (self.uid, key, value)
		#print command
		self.write_serial_string(command)

	def write_serial_string(self, string):
		print string
		for i in list(string):
			print i
			print i
			self.commander.write(i)
			time.sleep(0.001)

def main():

	ser = serial.Serial('COM6', baudrate=38400)

	firstUnit = ArduinoController(ser, '1111')
##	secondUnit = ArduinoController(ser, '2222')
##	thirdUnit = ArduinoController(ser, '3333')
##	forthUnit = ArduinoController(ser, '4444')
##	fifthUnit = ArduinoController(ser, '5555')

	firstUnit.start(180)
##	secondUnit.start(200)
##	thirdUnit.start(200)
##	forthUnit.start(200)
##	fifthUnit.start(200)

	time.sleep(2)

##	firstUnit.setSpeedRight(230)
##	firstUnit.setSpeedLeft(170)

##	time.sleep(2)

##	firstUnit.stop()
##	firstUnit.start(0)
##	firstUnit.setSpeedRight(-200)
##	firstUnit.setSpeedLeft(200)

##	time.sleep(2)

	#firstUnit.stop()
	#firstUnit.start(0)
##	firstUnit.setSpeedRight(200)
##	firstUnit.setSpeedLeft(-200)

##	time.sleep(2)

	firstUnit.stop()
##	secondUnit.stop()
##	thirdUnit.stop()
##	forthUnit.stop()
##	fifthUnit.stop()

	ser.close()

if __name__ == '__main__':
	main()
