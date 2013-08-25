"""Central model
This contains all info for the modules to use"""

import sys
import copy
import numpy as np
import cv2
import cv2.cv as cv

COLOR_DICT = {  'yellow'   : (np.array([10, 100, 100],np.uint8), np.array([40, 255, 255],np.uint8)),
        'red'    : (np.array([165, 145, 100],np.uint8),np.array([250, 210, 160],np.uint8)),
        'blue'    : (np.array([100, 70, 50],np.uint8), np.array([130, 255, 255],np.uint8)),
        'green'    : (np.array([40, 80, 30],np.uint8), np.array([70, 255, 255],np.uint8))
        }

class Vector():
    """Represents a two dimensional vector"""
        
    def __init__(self, x,  y, name = False,  board = False, owner = False):
        """Initializes the vector with values.
        Owner is the owning class, board is the containing board if exists.
        When a board is specified this vector will automatically update it with its location and will be indicated uniquely by its owner and name.
        (For example: a vector that the blue robot owns and represents location will have: self.name = 'location', self.owner = blueRobot)"""
        self.__x = x
        self.__y = y
        self.name = name
        self.board = board
        self.owner = owner
        # Initialize the vector on the board
        if False != self.board:
            self.board.addItem(x, y, self)
        
    def __eq__(self, other):
        if self.getX() == other.getX() and self.getY() == other.getY():
            return True
        return False
        
    def setValue(self, x,  y):
        """Sets the vector's values"""
        if False != self.board:
            self.board.removeItem(self.__x, self.__y,  self)
            self.board.addItem(x, y, self)
        self.__x = x
        self.__y = y
        
    def setX(self,  x):
        """Set x value"""
        self.setValue(x, self.getY())

    def getX(self):
        """Returns the robot's x value"""
        return self.__x

    def setY(self,  y):
        """Set y value"""
        self.setValue(self.getX(), y)
        
    def getY(self):
        """Returns the robot's y value"""
        return self.__y
        

class Color():
    """Represents a color vector with lower and upper values
    The robot's color is a range of colors with the format [(H, S, V) min,(H,S,V) max]"""
        
    def __init__(self, lower = False, upper = False):
        """Initializes the vector with values"""
        if (bool == type(lower) and lower == False) or (bool == type(upper) and upper == False):
            self.lower = False
            self.upper = False
        else:
            self.setColor(lower, upper)
        
    def setColor(self,  lower,  upper):
        """Sets the robot's color"""
        if False == self.checkRelation(lower, upper):
            raise Exception("Lower color value is not lower or equal color upper value")
        self.lower = lower
        self.upper = upper
        
    def getColor(self):
        """Gets the color"""
        return (self.lower,  self.upper)
        
    def checkRelation(self, lower, upper):
        """Checks the relation between lower and upper: If lower is indeed lower or equal, returns True"""
        for l,  u in zip(lower,  upper):
            if l > u:
                return False
        return True

class Robot():
    """This represents a single robot.
    Each of the values defaults to False untill defined"""
    
    def __init__(self,  board):
        """Initializes the robot"""
        self.color = Color()
        self.board = board
        self.location = Vector(0, 0, 'location', self.board, self)
        self.direction = Vector(1, 0)
        
class Board():
    """Represents a game board, defined by resolution.
    Every addition and removal of a square's content is done by adding an item or removing an item.
    A clear square is represented by an empty list."""
    
    def __init__(self,  dimension_x,  dimension_y):
        """Initializes a board with dimensions. 
        Note: if a dimension is 5, the index for it will be 0 to 4."""
        self.content = dimension_x*[[[]]*dimension_y]
        self.dimensions = Vector(dimension_x, dimension_y)
    
    def addItem(self,  x, y,  content):
        """Adds the content to a board square if not already in there"""
        if content not in self.content[x][y]:
            self.content[x][y].append(content)

    def removeItem(self,  x, y,  content):
        """Removes the content from a board square if it exists"""
        if content in self.content[x][y]:
            self.content[x][y].remove(content)

    def setContent(self,  x, y,  content):
        """Sets the content of a board square.
        Note: This should not be called as it overrides previous content! use addItem instead!"""
        self.content[x][y] = content
        
    def getItems(self,  x, y):
        """Gets a list of items in a board square"""
        return copy.deepcopy(self.content[x][y])
        
    def getDimensions(self):
        """Gets the vector representing the dimensions"""
        return copy.deepcopy(self.dimensions)
        
class Screen():
    """The screen projected by the projector"""
    # This is empty because the graphic module will determine this class
    
class CentralClass():
    """The central class contains all info for modules"""
    def __init__(self, board_x,  board_y):
        self.board = Board(board_x, board_y)
        self.screen = Screen()
        self.robots = [Robot(self.board)]
    
def main():
    """Main method - creates all threads"""
    central_class = CentralClass(4, 4)
    # Start all threads
    
    # Will remain active 
    
if "__main__" == __name__:
    main()
