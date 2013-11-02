"""
Achtung!
"""
import pygame
from collections import namedtuple
from vec2d import Vec2d

#
# Constants
#

DEBUG = True

Color = namedtuple('Color', ['name', 'value', 'valueRange'])

# TODO: set value range for openCV
COLORS = [
    Color('Black', (0, 0, 0), None),
    Color('Red', (255, 0, 0), None),
    Color('Green', (0, 255, 0), None),
    Color('Blue', (0, 0, 255), None),
    Color('Yellow', (255, 255, 0), None),
]
if DEBUG:
    COLORS = [COLORS[0]]

LEFT = -1
STRAIGHT = 0
RIGHT = 1

ROBOT_RADIUS = 5

GAME_WIDTH = 500
GAME_HIGHT = 500

FPS_LIMIT = 60

#
# Classes
#

class RobotNotFoundError(Exception):
    pass

class Trail:
    def __init__(self, surface, color):
        self.surface = surface
        self.color = color
        self.trail = []

    def addPoint(self, point):
        self.trail.append(point)

    def draw(self):
        #print self.trail
        previous_point = self.trail[0]
        for point in self.trail[1:]:
            pygame.draw.line(self.surface, self.color.value, previous_point, point, ROBOT_RADIUS)
            previous_point = point

class Player:
    def __init__(self, surface, color):
        self.surface = surface
        self.color = color
        self.alive = True
        self.direction = None
        self.position = None
        self.trail = Trail(surface, color)

        if DEBUG:
            self.position = Vec2d(GAME_WIDTH / 2, GAME_HIGHT / 2)
            self.directionVector = Vec2d(1, 0)

    def _move(self):
        assert DEBUG
        ROTATION_DEGREES = 3
        SPEED = 1.5
        if self.direction == LEFT:
            self.directionVector.rotate(-ROTATION_DEGREES)
        elif self.direction == RIGHT:
            self.directionVector.rotate(ROTATION_DEGREES)

        self.position += (self.directionVector * SPEED)

    def getRobotPositionFromCamera(self):
        """Get Position from camera via opencv. Throw RobotNotFoundError if robot not found."""
        if DEBUG:
            return self.position

    def updatePosition(self):
        self.position = self.getRobotPositionFromCamera()
        self.trail.addPoint(Vec2d(self.position))

    def getDirectionFromController(self):
        """Get direction from watch controller"""
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
            return direction

    def updateDirection(self):
        self.direction = self.getDirectionFromController()
        self.sendDirectionToRobot()

    def die(self):
        self.alive = False
        self.sendStopToRobot()
        self.electrify()

    def sendDirectionToRobot(self):
        """Send direction to robot via xbee"""
        pass

    def sendStartToRobot(self):
        """Send Start command (start moving) to the robot via xbee"""
        pass

    def sendStopToRobot(self):
        """Send Stop command (stop moving) to the robot via xbee"""
        pass

    def electrify(self):
        """Shock player with electric pulse"""
        pass

class Game:
    def __init__(self, width, hight):
        self.width = width
        self.hight = hight

        pygame.init()
        self.screen = pygame.display.set_mode((width, hight))
        self.surface = pygame.Surface(self.screen.get_size())
        self.clock = pygame.time.Clock()

        self.players = [Player(self.surface, color) for color in COLORS]

    def start(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()

            for player in self.players:
                try:
                    player.updatePosition()
                except RobotNotFoundError:
                    player.die()
                player.updateDirection()

            self.clearSurface()
            for player in self.players:
                player.trail.draw()
            self.updateDisplay()

##            for robot in robots:
##                #TODO: check robot colision with walls
##
##                for trail in (robot.trail for robot in robots):
##                    if self.robotColidesWithTrail(robot, trail):
##                        robot.die()
##
##            # Check end conditions
##            living_robots = [robot for robot in robots if robot.alive]
##            if len(living_robots) == 0:
##                end_state = 'draw'
##                break
##            elif len(living_robots) == 1:
##                end_state = 'win'
##                winner = living_robots[0]
##                if not DEBUG:
##                    break

            if DEBUG:
                for player in self.players:
                    player._move()

            self.tick()

        if end_state == 'draw':
            message = 'Draw.'
        elif end_state == 'win':
            message = 'The winner is %s!' % winner.color.name
        else:
            message = 'WTF?'

        print message

    def clearSurface(self):
        self.surface.fill((255, 255, 255))

    def updateDisplay(self):
        self.screen.blit(self.surface, (0, 0))
        pygame.display.flip()

##    def robotColidesWithWalls(self, robot):
##        pass
##
##    def robotColidesWithTrail(self, robot, trail):
##        pass

    def tick(self):
        """Wait for the next game tick"""
        self.clock.tick(FPS_LIMIT)

def main():
    game = Game(GAME_WIDTH, GAME_HIGHT)
    game.start()

if "__main__" == __name__:
    main()
