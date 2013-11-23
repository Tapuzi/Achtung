'''This class includes controllers classes'''

from flags import *
import pygame
import uberclock02 as uberclock
import math

LEFT = -1
STRAIGHT = 0
RIGHT = 1

class Controller:
    """Abstract base class for controllers"""
    def getDirection(self):
        raise NotImplementedError()
        
    def getType(self):
        return self.__class__.__name__

class MouseController(Controller):
    def __init__(self, additional_info = ''):
        self.additional_info = additional_info

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
        
    def getAdditionalInfo(self):
        return self.additional_info

class GamepadController(Controller):
    # TODO: Implement if we want to add support, in case multiple Watches don't work well.
    def __init__(self, additional_info = ''):
        self.additional_info = additional_info

    def getDirection(self):
        pass
        
    def getAdditionalInfo(self):
        return self.additional_info

class TouchpadController(Controller):
    # TODO: If we get really desperate about controllers,
    #       we could implement a controller from the laptop's touchpad
    #       by assigning the left side of it to LEFT and right side to RIGHT.
    def __init__(self, additional_info = ''):
       self.additional_info = additional_info
        
    def getDirection(self):
        pass
        
    def getAdditionalInfo(self):
        return self.additional_info

class KeyboardController(Controller):
    def __init__(self, left_key , right_key, additional_info = ''):
        self.left_key = left_key
        self.right_key = right_key
        self.additional_info = additional_info

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
        
    def getAdditionalInfo(self):
        return self.additional_info

class XboxController(Controller):
    def __init__(self, index, additional_info = ''):
        self.controller = pygame.joystick.Joystick(index)
        self.controller.init()
        self.x_direction = 0
        self.additional_info = additional_info

    def getDirection(self):
        self.x_direction = self.controller.get_axis(4)
        if math.fabs(self.x_direction) < 0.95:
            self.x_direction = 0
        direction = STRAIGHT
        if self.x_direction < 0:
            direction = LEFT
        elif self.x_direction > 0:
            direction = RIGHT
        return direction
        
    def getAdditionalInfo(self):
        return self.additional_info

class WatchController(Controller):
    def __init__(self, comPort, deviceId, additional_info = ''):
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
        
    def getAdditionalInfo(self):
        return self.additional_info

def getDefaultControllers(amount):
    watch_controllers = getWatchControllers()
    xbox_controller = getXboxControllers()
    mouse_controller = [MouseController()] if USE_MOUSE else []
    keyboard_controllers = [
        KeyboardController(pygame.K_LEFT, pygame.K_RIGHT, "Left key, Right key"),
        KeyboardController(pygame.K_z, pygame.K_c, "z key, c key"),
        KeyboardController(pygame.K_KP4, pygame.K_KP6, "4 key, 6 key"),
        KeyboardController(pygame.K_b, pygame.K_m, "b key, m key"),
    ]
    controllers = watch_controllers + xbox_controller + mouse_controller + keyboard_controllers
    return controllers[:amount]
    
def getControllers():
    watch_controllers = getWatchControllers()
    xbox_controller = getXboxControllers()
    mouse_controller = [MouseController()] if USE_MOUSE else []
    keyboard_controllers = [
        KeyboardController(pygame.K_LEFT, pygame.K_RIGHT, "Left key, Right key"),
        KeyboardController(pygame.K_z, pygame.K_c, "z key, c key"),
        KeyboardController(pygame.K_KP4, pygame.K_KP6, "4 key, 6 key"),
        KeyboardController(pygame.K_b, pygame.K_m, "b key, m key"),
    ]
    controllers = watch_controllers + xbox_controller + mouse_controller + keyboard_controllers
    return controllers

def getXboxControllers():
    return [XboxController(i) for i in xrange(pygame.joystick.get_count())]

def getWatchControllers():
    #TODO: Detect connected watches, and return WatchController list
    #      (try using serial.tools.list_ports.comports())
    return []
