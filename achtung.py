"""Central model
This contains all info for the modules to use"""

import sys
import copy
import numpy as np
import cv2
import cv2.cv as cv
import pygame
from collections import namedtuple
from vec2d import Vec2d

DEBUG = True

#COLOR_DICT = {  'yellow'   : (np.array([10, 100, 100],np.uint8), np.array([40, 255, 255],np.uint8)),
#        'red'    : (np.array([165, 145, 100],np.uint8),np.array([250, 210, 160],np.uint8)),
#        'blue'    : (np.array([100, 70, 50],np.uint8), np.array([130, 255, 255],np.uint8)),
#        'green'    : (np.array([40, 80, 30],np.uint8), np.array([70, 255, 255],np.uint8))
#        }
        
    
Color = namedtuple('Color', ['name', 'value', 'valueRange'])    

#RED = Color('Red', (255, 0, 0), (np.array([165, 145, 100],np.uint8),np.array([250, 210, 160],np.uint8)))
#GREEN = Color('Green', (0, 255, 0), (np.array([40, 80, 30],np.uint8), np.array([70, 255, 255],np.uint8)))
#BLUE = Color('Blue', (0, 0, 255), (np.array([40, 80, 30],np.uint8), np.array([70, 255, 255],np.uint8)))

RED = Color('Red', (255, 0, 0), None)
GREEN = Color('Green', (0, 255, 0), None)
BLUE = Color('Blue', (0, 0, 255), None)
BLACK = Color('Black', (0, 0, 0), None)
    
LEFT = -1
STRAIGHT = 0
RIGHT = 1
        
ROBOT_RADIUS = 50

# class Color():
    # """Represents a color vector with lower and upper values
    # The robot's color is a range of colors with the format [(H, S, V) min,(H,S,V) max]"""
        
    # def __init__(self, lower = False, upper = False):
        # """Initializes the vector with values"""
        # if (bool == type(lower) and lower == False) or (bool == type(upper) and upper == False):
            # self.lower = False
            # self.upper = False
        # else:
            # self.setColor(lower, upper)
        
    # def setColor(self,  lower,  upper):
        # """Sets the robot's color"""
        # if False == self.checkRelation(lower, upper):
            # raise Exception("Lower color value is not lower or equal color upper value")
        # self.lower = lower
        # self.upper = upper
        
    # def getColor(self):
        # """Gets the color"""
        # return (self.lower,  self.upper)
        
    # def checkRelation(self, lower, upper):
        # """Checks the relation between lower and upper: If lower is indeed lower or equal, returns True"""
        # for l,  u in zip(lower,  upper):
            # if l > u:
                # return False
        # return True

class Robot():
    def __init__(self,  color, x, y):
        self.color = color
        self.alive = True
        self.direction = STRAIGHT
        self.x = x
        self.y = y
        self.trail = [(x, y)]
        
        if DEBUG:
            self.directionVector = Vec2d(1, 0)
        
    def setDirection(self, direction):
        self.direction = direction
        self.sendDirection()
        
    def updatePosition(self, x, y):
        self.x = x
        self.y = y
        self.trail.append((x, y))
        
    def die(self):
        self.alive = False
        self.sendStop()
        self.electrifyPlayer()
        
    def sendDirection(self):
        """Send direction to robot via xbee"""
        pass
        
    def sendGo(self):
        """Send Go (start moving) to the robot via xbee"""
        pass
        
    def sendStop(self):
        """Send Stop (stop moving) to the robot via xbee"""
        pass
        
    def electrifyPlayer(self):
        pass
    
class Game():
    def __init__(self, width, hight):
        self.width = width
        self.hight = hight
        if DEBUG:
            self.robots_position = {BLACK: (250, 250)}
            
        pygame.init()
        self.screen = pygame.display.set_mode((width, hight))
        self.surface = pygame.Surface(self.screen.get_size())
        self.clock = pygame.time.Clock()
        
    def start(self):
        # Initialization
        print 'Init'
        robot_positions = self.getRobotsPosition()
        robots = [Robot(color, x, y) for color, (x, y) in robot_positions.items()]
        if DEBUG:
            self.robots = robots
        color_to_robots = {robot.color: robot for robot in robots}
        
        # Main loop
        print 'Main loop'
        while True:
            self.tick()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()
            
            controllers_states = self.getControlersState()
            
            for color, direction in controllers_states.items():
                robot = color_to_robots[color]
                robot.setDirection(direction)
                
            robot_positions = self.getRobotsPosition()
            # Todo - check if a robot is missing, and remove it.
            
            for color, (x, y) in robot_positions.items():
                robot = color_to_robots[color]
                robot.updatePosition(x, y)
                
            self.clearScreen()
            for robot in robots:
                self.drawTrail(robot.trail, robot.color.value)
            self.screen.blit(self.surface, (0, 0))
            pygame.display.flip()
                
            for robot in robots:
                #TODO: check robot colision with walls
                
                for trail in (robot.trail for robot in robots):
                    if self.robotColidesWithTrail(robot, trail):
                        robot.die()
                    
            # Check end conditions
            living_robots = [robot for robot in robots if robot.alive]
            if len(living_robots) == 0:
                end_state = 'draw'
                break
            elif len(living_robots) == 1:
                end_state = 'win'
                winner = living_robots[0]
                if not DEBUG:
                    break
                    
            self.tick()
        
        if end_state == 'draw':
            message = 'Draw.'
        elif end_state == 'win':
            message = 'The winner is %s!' % winner.color.name
        else:
            message = 'WTF?'
            
        print message
            
    def clearScreen(self):
        self.surface.fill((255, 255, 255))
        
    def drawTrail(self, trail, color):
        previous = trail[0]
        for current in trail[1:]:
            pygame.draw.line(self.surface, color, previous, current, 5)
            previous = current
        
    def getControlersState(self):
        """Return a dictionary of color to direction"""
        if DEBUG:
            pressed_keys = pygame.key.get_pressed()
            left_pressed = pressed_keys[pygame.K_LEFT]
            right_pressed = pressed_keys[pygame.K_RIGHT]
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
            return {BLACK: direction}
        
    def getRobotsPosition(self):
        """Return a dictionary of color to (x,y) position)"""
        if DEBUG:
            return self.robots_position
        
    def robotColidesWithWalls(self, robot):
        pass
        
    def robotColidesWithTrail(self, robot, trail):
        pass
        
    def tick(self):
        """Wait for the next game tick"""
        self.clock.tick(60)
        if DEBUG:
            for robot in self.robots:
                ROTATION_DEGREES = 3
                SPEED = 3.5
                if robot.direction == LEFT:
                    robot.directionVector.rotate(-ROTATION_DEGREES)
                elif robot.direction == RIGHT:
                    robot.directionVector.rotate(ROTATION_DEGREES)
                
                new_position = Vec2d(robot.x, robot.y) + (robot.directionVector * SPEED)
                self.robots_position[robot.color] = (new_position.x, new_position.y)
                
                    
    
def main():
    game = Game(500, 500)
    game.start()
    
if "__main__" == __name__:
    main()
