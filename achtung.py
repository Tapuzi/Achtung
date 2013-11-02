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

ROBOT_RADIUS = 7
COLLISTION_RADIUS = ROBOT_RADIUS - 2

GAME_WIDTH = 500
GAME_HIGHT = 500

FPS_LIMIT = 60

OVERLAP_COLLISION_THRESHOLD = 10

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

    def draw(self):
        self.game_surface.blit(self.surface, (0, 0))

class Player:
    def __init__(self, game_surface, color):
        self.game_surface = game_surface
        self.surface = pygame.Surface((GAME_WIDTH, GAME_HIGHT), flags=pygame.SRCALPHA)
        self.color = color
        self.alive = True
        self.direction = None
        self.position = None
        self.trail = Trail(self.game_surface, color)

        if DEBUG:
            self.position = Vec2d(GAME_WIDTH / 2, GAME_HIGHT / 2)
            self.directionVector = Vec2d(1, 0)

    def _move(self):
        assert DEBUG
        ROTATION_DEGREES = 3.0
        SPEED = 2
        if self.direction == LEFT:
            self.directionVector.rotate(-ROTATION_DEGREES)
        elif self.direction == RIGHT:
            self.directionVector.rotate(ROTATION_DEGREES)

        self.position += (self.directionVector * SPEED)

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
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((GAME_WIDTH, GAME_HIGHT))
        self.surface = pygame.Surface(self.screen.get_size())
        self.clock = pygame.time.Clock()

        self.players = [Player(self.surface, color) for color in COLORS]

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
                if not DEBUG:
                    break

            if DEBUG:
                for player in players_alive:
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
