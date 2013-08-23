"""Central model
This contains all info for the modules to use"""

import sys

class Vector():
    """Represents a two dimensional vector"""
    
    def __init__(self):
        """Initializes the vector"""
        self.x = False
        self.y = False
        
    def __init__(self,  x,  y):
        """Initializes the vector with values"""
        self.x = x
        self.y = y
        
    def __eq__(self, other):
        if self.x == other.x and self.y == other.y:
            return True
        return False

class Robot():
    """This represents a single robot.
    Each of the values defaults to False untill defined"""
    def __init__(self):
        """Initializes the robot"""
        self.location = Vector()
        self.direction = Vector()
        self.color = False
        
    def setX(self,  x):
        """Set x value"""
        self.location.x = x

    def getX(self):
        """Returns the robot's x value"""
        return self.location.x

    def setY(self,  y):
        """Set y value"""
        self.location.y = y
        
    def getY(self):
        """Returns the robot's y value"""
        return self.location.y
        
    def setLocation(self,  x,  y):
        """Set the x and y values"""
        self.location.setX(x)
        self.location.setY(y)
        
    def setLocation(self,  vector):
        """Set the x and y values by vector value"""
        self.location.setX(vector.x)
        self.location.setY(vector.y)

    def getLocation(self):
        """Returns the location of the robot as a vector"""
        return Vector(self.location.x, self.location.y)
        
    def setDirection(self,  x,  y):
        """Set direction by x,y values"""
        self.direction.x = x
        self.direction.y = y
        
    def setDirection(self,  vector):
        """Set direction by vector value"""
        self.setDirection(vector.x,  vector.y)
        
    def getDirection(self):
        """Returns the robot's direction as a vector"""
        return Vector(self.direction.x, self.direction.y)
        
    def setColor(self,  color):
        """Sets the robot's color"""
        self.color = color
        
    def getColor(self):
        """Returns the robot's set color"""
        return self.color
        
class Board():
    """Represents a game board, defined by resolution"""
    
    def __init__(self,  dimension_x,  dimension_y):
        """Initializes a board with dimensions. 
        Note: if a dimension is 5, the index for it will be 0 to 4."""
        self.content = dimension_x*[[0]*dimension_y]
    
    def setContent(self,  vector,  content):
        """Sets the content of a board square"""
        self.content[vector.x, vector.y] = content
        
    def getContent(self,  vector):
        """Gets the content of a board square"""
        return self.content[vector.x, vector.y]
        
class Screen():
    """The screen projected by the projector"""
    # This is empty because the graphic module will determine this class
    
class CentralClass():
    """The central class contains all info for modules"""
    def __init__(self, board_x,  board_y):
        self.robots = []
        self.board = Board(board_x, board_y)
        self.screen = Screen()
    
def main():
    """Main method - creates all threads"""
    central_class = CentralClass(4, 4)
    # Start all threads
    
    # Will remain active 
    
if "__main__" == __name__:
    main()
