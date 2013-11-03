"""
Achtung!
"""
import pygame
from collections import namedtuple
from vec2d import Vec2d
import uberclock02 as uberclock
import random

##
## TODO:
##     - Add sounds (start, player death, draw, win, ... maybe use DOTA/MortalKombat's announcer?)
##     - Add full screen support (with black stripes...)
##     - Add rounds and scores
##     - Support high speeds by drawing "circle lines" from the last point to the current point (?)
##       or try using http://pygamedraw.wordpress.com/ for trail drawing.
##     - Also consider using pygamedraw to eliminate the trail hole bug.
##       (using proper lines instead of circles might solve it)
##     - Profile the game and improve performance (it seems that with multiple players / bigger window,
##       The drawing / collision detection slows the game down.
##       - Try to do things in parallel? (collision detection for example)
##       - Try to limit the mask overlap test are to that of the player's position (and radius)
##       - Maybe just use a lower target framerate
##     - Add a mode in between round that allows to drive robots back to the middle of the board?
##     - Add bonuses (speed up/down, control reverse, players swap, electrify etc...)
##

#
# Constants
#

DEBUG = True

# Set to false to debug with watch controllers
DEBUG_KEYBOARD = True

DEBUG_KEYBOARD_TWO_PLAYERS = False

DEBUG_MOUSE = False

DEBUG_SINGLE_PLAYER = DEBUG and not DEBUG_KEYBOARD_TWO_PLAYERS

#####


Color = namedtuple('Color', ['name', 'value', 'value_range'])

# TODO: set value range for openCV
COLORS = [
    Color('Black', (0, 0, 0), None),
    Color('Red', (255, 0, 0), None),
    Color('Green', (0, 255, 0), None),
    Color('Blue', (0, 0, 255), None),
    Color('Yellow', (255, 255, 0), None),
]

IDS = ['1337' for color in COLORS]
COMPORTS = ['COM10']

LEFT = -1
STRAIGHT = 0
RIGHT = 1

ROBOT_RADIUS = 7
COLLISTION_RADIUS = ROBOT_RADIUS - 2

GAME_WIDTH = 500
GAME_HIGHT = 500

FPS_LIMIT = 60

OVERLAP_COLLISION_THRESHOLD = 10

TIME_TO_HOLE_MIN = 1.25 * 1000
TIME_TO_HOLE_MAX = 1.75 * 1000
HOLE_TIME_INTERVAL = 0.3 * 1000

#
# Classes
#

class RobotNotFoundError(Exception):
    pass

class Trail:
    def __init__(self, game_surface, color):
        self.game_surface = game_surface
        self.surface = pygame.Surface((GAME_WIDTH, GAME_HIGHT), flags=pygame.SRCALPHA)
        self.color = color
        self.last_point = None
        self.last_point_surface = pygame.Surface((GAME_WIDTH, GAME_HIGHT), flags=pygame.SRCALPHA)

    def addPoint(self, point):
        int_point = (int(point.x), int(point.y))

        if self.last_point is not None:
            # Clear current point to avoid collision detection issues
            pygame.draw.circle(self.last_point_surface, (0, 0, 0, 0), int_point, ROBOT_RADIUS)
            self.surface.blit(self.last_point_surface, (0, 0))

        self.last_point = point
        self.last_point_surface.fill((0, 0, 0, 0))
        pygame.draw.circle(self.last_point_surface, self.color.value, int_point, ROBOT_RADIUS)

    def addInvisiblePoint(self, point):
        int_point = (int(point.x), int(point.y))
        last_point_int = (int(self.last_point.x), int(self.last_point.y))

        self.last_point_surface.fill((0, 0, 0, 0))
        pygame.draw.circle(self.last_point_surface, self.color.value, last_point_int, ROBOT_RADIUS)

        pygame.draw.circle(self.last_point_surface, (0, 0, 0, 0), int_point, ROBOT_RADIUS)
        self.surface.blit(self.last_point_surface, (0, 0))

    def draw(self):
        self.game_surface.blit(self.surface, (0, 0))

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
        elif not left_pressed and not right_pressed:
            direction = STRAIGHT
        elif left_pressed and right_pressed:
            direction = STRAIGHT
        else:
            raise Exception('wtf')

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


class Player:
    def __init__(self, game_surface, color, controller):
        self.game_surface = game_surface
        self.surface = pygame.Surface((GAME_WIDTH, GAME_HIGHT), flags=pygame.SRCALPHA)
        self.color = color
        self.alive = True
        self.direction = None
        self.position = None
        self.trail = Trail(self.game_surface, color)
        self.controller = controller

        self._time_of_next_hole = None
        self.resetTimeOfNextHole()

        self._time_of_hole_end = None
        self.resetTimeOfHoleEnd()

        self._creating_hole = False
        # Reset timers
        self.creatingHole()


        if DEBUG:
            self.position = Vec2d(GAME_WIDTH / 2, GAME_HIGHT / 2)
            self.direction_vector = Vec2d(1, 0)

    def resetTimeOfNextHole(self):
        current_time = pygame.time.get_ticks()
        time_to_next_hole = random.uniform(TIME_TO_HOLE_MIN, TIME_TO_HOLE_MAX)
        self._time_of_next_hole = current_time + time_to_next_hole

    def resetTimeOfHoleEnd(self):
        current_time = pygame.time.get_ticks()
        self._time_of_hole_end = current_time + HOLE_TIME_INTERVAL

    def creatingHole(self):
        """Return True/False whether the player is creating a hole right now or not"""
        current_time = pygame.time.get_ticks()

        if self._creating_hole:
            if current_time >= self._time_of_hole_end:
                self._creating_hole = False
                self.resetTimeOfNextHole()
        else:
            if current_time >= self._time_of_next_hole:
                self._creating_hole = True
                self.resetTimeOfHoleEnd()

        return self._creating_hole


    def _move(self):
        assert DEBUG
        ROTATION_DEGREES = 3.0
        SPEED = 2
        if self.direction == LEFT:
            self.direction_vector.rotate(-ROTATION_DEGREES)
        elif self.direction == RIGHT:
            self.direction_vector.rotate(ROTATION_DEGREES)

        self.position += (self.direction_vector * SPEED)

    def draw(self):
        self.game_surface.blit(self.surface, (0,0))

    def getRobotPositionFromCamera(self):
        """Get Position from camera via opencv. Throw RobotNotFoundError if robot not found."""
        if DEBUG:
            return self.position

    def updatePosition(self):
        self.position = self.getRobotPositionFromCamera()
        self.surface.fill((0, 0 ,0, 0))
        int_position = (int(self.position.x), int(self.position.y))
        if DEBUG:
            color = (90, 180, 90)
        else:
            color = self.color.value
        pygame.draw.circle(self.surface, color, int_position, ROBOT_RADIUS)
        if self.creatingHole():
           self.trail.addInvisiblePoint(Vec2d(self.position))
        else:
            self.trail.addPoint(Vec2d(self.position))

    def updateDirection(self):
        self.direction = self.controller.getDirection()
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
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((GAME_WIDTH, GAME_HIGHT))
        self.surface = pygame.Surface(self.screen.get_size())
        self.clock = pygame.time.Clock()

        if DEBUG_KEYBOARD:
            self.controllers = [KeyboardController(pygame.K_LEFT, pygame.K_RIGHT)]
            if DEBUG_KEYBOARD_TWO_PLAYERS:
                self.controllers.append(KeyboardController(pygame.K_z, pygame.K_c))
        elif DEBUG_MOUSE:
            self.controllers = [MouseController()]
        else:
            self.controllers = [WatchController(port, id) for port, id in zip(COMPORTS, IDS)]

        self.players = [Player(self.surface, color, controller) for color, controller in zip(COLORS, self.controllers)]

        if DEBUG_KEYBOARD_TWO_PLAYERS:
            self.players[1].position.y -= 100

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pygame.quit()

    def start(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()

            players_alive = [player for player in self.players if player.alive]
            for player in players_alive:
                try:
                    player.updatePosition()
                except RobotNotFoundError:
                    player.die()
                    players_alive.remove(player)
                player.updateDirection()

            self.clearSurface()
            for player in self.players:
                player.trail.draw()
                player.draw()
            self.updateDisplay()

            for player in players_alive:
                if self.playerColidesWithWalls(player):
                    player.die()

                for trail in (player.trail for player in self.players):
                    if self.playerColidesWithTrail(player, trail):
                        player.die()
            players_alive = [player for player in self.players if player.alive]


            # Check end conditions
            if len(players_alive) == 0:
                end_state = 'draw'
                break
            elif len(players_alive) == 1:
                end_state = 'win'
                winner = players_alive[0]
                if not DEBUG_SINGLE_PLAYER:
                    break

            if DEBUG:
                for player in players_alive:
                    player._move()

            self.tick()

        if end_state == 'draw':
            message = 'Draw.'
        elif end_state == 'win':
            message = '%s is he Winner!' % winner.color.name
        else:
            message = 'WTF?'

        print message

    def clearSurface(self):
        self.surface.fill((255, 255, 255))

    def updateDisplay(self):
        self.screen.blit(self.surface, (0, 0))
        pygame.display.flip()

    def playerColidesWithWalls(self, player):
        x, y = player.position
        left_wall_collision = x - COLLISTION_RADIUS <= 0
        top_wall_collision = y - COLLISTION_RADIUS <= 0
        right_wall_collision = x + COLLISTION_RADIUS >= GAME_WIDTH
        bottom_wall_collision = y + COLLISTION_RADIUS >= GAME_HIGHT
        any_wall_collision = left_wall_collision or top_wall_collision or right_wall_collision or bottom_wall_collision
        return any_wall_collision

    def playerColidesWithTrail(self, player, trail):
        player_mask = pygame.mask.from_surface(player.surface)
        trail_mask = pygame.mask.from_surface(trail.surface)

        overlapping_pixels = trail_mask.overlap_area(player_mask, (0, 0))
        if overlapping_pixels > OVERLAP_COLLISION_THRESHOLD:
            return True
        else:
            return False

    def tick(self):
        """Wait for the next game tick"""
        self.clock.tick(FPS_LIMIT)
        current_fps = self.clock.get_fps()
        pygame.display.set_caption("FPS: %f" % current_fps)

def main():
    with Game() as game:
        game.start()

if "__main__" == __name__:
    main()
