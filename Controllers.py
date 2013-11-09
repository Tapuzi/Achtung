'''This class includes controllers classes'''

from flags import *
import pygame
if not DEBUG_KEYBOARD:
    import uberclock02 as uberclock

LEFT = -1
STRAIGHT = 0
RIGHT = 1

class Controller:
    """Abstract base class for controllers"""
    def getDirection(self):
        raise NotImplementedError()

class MouseController(Controller):
    def __init__(self):
        pass

    def getDirection(self):
        pressed_keys = pygame.mouse.get_pressed()

        left_pressed = pressed_keys[0]
        right_pressed = pressed_keys[2]

        if left_pressed and not right_pressed:
            direction = LEFT
        elif not left_pressed and right_pressed:
            direction = RIGHT
        elif not left_pressed and not right_pressed:
            direction = STRAIGHT
        elif left_pressed and right_pressed:
            direction = STRAIGHT
        else:
            raise Exception('wtf')

        return direction

class GamepadController(Controller):
    # TODO: Implement if we want to add support, in case multiple Watches don't work well.
    def __init__(self):
        pass

    def getDirection(self):
        pass

class TouchpadController(Controller):
    # TODO: If we get really desperate about controllers,
    #       we could implement a controller from the laptop's touchpad
    #       by assigning the left side of it to LEFT and right side to RIGHT.
    def __init__(self):
        pass

    def getDirection(self):
        pass

class KeyboardController(Controller):
    def __init__(self, left_key, right_key):
        self.left_key = left_key
        self.right_key = right_key

    def getDirection(self):
        pressed_keys = pygame.key.get_pressed()

        left_pressed = pressed_keys[self.left_key]
        right_pressed = pressed_keys[self.right_key]

        if left_pressed and not right_pressed:
            direction = LEFT
        elif not left_pressed and right_pressed:
            direction = RIGHT
        else:
            direction = STRAIGHT

        return direction

class WatchController(Controller):
    def __init__(self, comPort, deviceId):
        self.deviceId = deviceId
        self.lastMessage = {'buttons': 0, 'temp': 0, 'accel_z': 0, 'accel_x': 0, 'accel_y': 0, 'alt': 0}
        # Connect to the watch
        self.ap_socket = uberclock.accessPointSocket(comPort)
        # Turn on watch
        self.ap_socket.start()
        # Create a device connection object and link it to the watch socket
        self.device_connection = uberclock.deviceConnection(self.ap_socket, deviceId)
        try:
            print "Waiting for connection of id %s..." % deviceId
            self.device_connection.connect_to_device() # NOTE: Blocking!
        except KeyboardInterrupt:
            raise Exception("No controller")


    def getState(self):
        # Make sure device is connected
        if not self.device_connection.is_device_connected():
            raise Exception("Device Disconnected: %s" % deviceId)

        # Get the latest state
        messages = self.device_connection.receive()

        if None == messages:
            return self.lastMessage

        self.lastMessage = messages[-1]
        return self.lastMessage

    def getOrientation(self):
        state = self.getState()
        print state
        if 20 > state['accel_x'] > 3:
            return LEFT

        if 238 < state['accel_x'] < 255:
            return RIGHT

        return STRAIGHT

    def getDirection(self):
        return self.getOrientation()