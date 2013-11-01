"""Central model
This contains all info for the modules to use"""

import sys
import copy
import numpy as np
import cv2
import cv2.cv as cv
import pygame
from collections import namedtuple

#COLOR_DICT = {  'yellow'   : (np.array([10, 100, 100],np.uint8), np.array([40, 255, 255],np.uint8)),
#        'red'    : (np.array([165, 145, 100],np.uint8),np.array([250, 210, 160],np.uint8)),
#        'blue'    : (np.array([100, 70, 50],np.uint8), np.array([130, 255, 255],np.uint8)),
#        'green'    : (np.array([40, 80, 30],np.uint8), np.array([70, 255, 255],np.uint8))
#        }
		
	
Color = namedtuple('Color', ['name', 'value', 'valueRange'])	

RED = Color('Red', (255, 0, 0), (np.array([165, 145, 100],np.uint8),np.array([250, 210, 160],np.uint8)))
GREEN = Color('Green', (0, 255, 0), (np.array([40, 80, 30],np.uint8), np.array([70, 255, 255],np.uint8)))
BLUE = Color('Blue', (0, 0, 255), (np.array([40, 80, 30],np.uint8), np.array([70, 255, 255],np.uint8)))

COLORS = [RED, GREEN, BLUE]
	
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
        
	def setDirection(direction)
		self.direction = direction
		sendDirection()
		
	def updatePosition(x, y):
		self.x = x
		self.y = y
		self.trail.append(x, y)
		
	def die():
		self.alive = False
		sendStop()
		electrifyPlayer()
		
	def sendDirection():
		"""Send direction to robot via xbee"""
		pass
		
	def sendGo():
		"""Send Go (start moving) to the robot via xbee"""
		pass
		
	def sendStop():
		"""Send Stop (stop moving) to the robot via xbee"""
		pass
		
	def electrifyPlayer():
		pass
    
class Game():
    def __init__(self, width, hight):
        self.width = width
		self.hight = hight
		
	def start():
		# Initialization
		robot_positions = getRobotsPosition()
		robots = [Robot(color, x, y) for color, (x, y) in robot_positions.items()]
		color_to_robots = {robot.color: robot for robot in robots}
		
		# Main loop
		while True:
			controllers_states = getControlersState()
			
			for color, direction in controllers_states.items:
				robot = color_to_robots[color]
				robot.setDirection(direction)
				
			robot_positions = getRobotsPosition()
			# Todo - check if a robot is missing, and remove it.
			
			for color, (x, y) in robots_positions:
				robot = color_to_robots[color]
				robot.setPosition(x, y)
				
			clearScreen()
			for trail in (robot.trail for robot in robots):
				drawTrail(trail)
				
			for robot in robots:
				#TODO: check robot colision with walls
				
				for trail in (robot.trail for robot in robots):
					if robotColidesWithTrail(robot, trail):
						robot.die()
					
			# Check end conditions
			living_robots = [robot for robot in robots if robot.isAlive]
			if len(living_robots) == 0:
				end_state = 'draw'
				break
			elif len(living_robots) == 1:
				end_state = 'win'
				winner = living_robots[0]
				break
					
			tick()
		
		if end_state == 'draw':
			message = 'Draw.'
		elif end_state == 'win':
			message = 'The winner is %s!' % winner.color.name
		else:
			message = 'WTF?'
			
		print message
			
	def clearScreen():
		pass
		
	def drawTrail(trail):
		pass
		
	def getControlersState():
		"""Return a dictionary of color to direction"""
		pass
		
	def getRobotsPosition():
		"""Return a dictionary of color to (x,y) position)"""
		pass
		
	def robotColidesWithWalls(robot):
		pass
		
	def robotColidesWithTrail(robot, trail):
		pass
		
	def tick():
		"""Wait for the next game tick"""
		import time
		time.sleep(0.01)
		#pass
    
def main():
    game = Game(1000, 1000)
	game.start()
    
if "__main__" == __name__:
    main()
