"""
Achtung!
"""
from flags import *
from ArduinoSerial import ArduinoController

import serial
import pygame
from collections import namedtuple
from vec2d import Vec2d
import random
import numpy
import os
from os import path
import atexit
import menu

if DEBUG_WEBCAM:
    from WebCam import *
from Controllers import *

if DEBUG_WEBCAM:
    import cv2
    import cv2.cv as cv

##
## TODO:
##     - Add more bonuses (speed up/down, control reverse, players swap, electrify etc...)
##     - Add a margin where game info is displayed
##     - Add white frame around board edges
##     - Show game info (Name, scores, round winner etc...)
##     - Add more sounds (player death, draw, win, ... maybe use DOTA/MortalKombat's announcer?)
##
## Fixes:
##    - Currently taking SpeedDown bonus twice in debug mode (not real robots...)
##      causes the player to collide with itself. Fix this by making TRAIL_NON_COLLIDING_LAST_POINTS dynamic?
##
## Improvements:
##     - Support high speeds by drawing "circle lines" from the last point to the current point (?)
##       or try using http://pygamedraw.wordpress.com/ for trail drawing.
##     - Profile the game and improve performance (it seems that with multiple players / bigger window,
##       The drawing / collision detection slows the game down.
##       - Try to do things in parallel? (collision detection for example)
##

#
# Module init
#

pygame.init()

@atexit.register
def cleanup():
    #TODO: stop all robots
    pygame.quit()

def exit_():
    cleanup()
    exit()

#
# Constants
#

ROOT_DIR = path.abspath(path.dirname(__file__))
SOUND_DIR = path.join(ROOT_DIR, 'sound')
MUSIC_DIR = path.join(ROOT_DIR, 'music')
IMAGES_DIR = path.join(ROOT_DIR, 'Images')

def list_files_full_path(directory):
    entries = [path.join(directory, entry) for entry in os.listdir(directory)]
    files = [entry for entry in entries if path.isfile(entry)]
    return files

SOUND_FILES = list_files_full_path(SOUND_DIR)
MUSIC_FILES = list_files_full_path(MUSIC_DIR)
IMAGE_FILES = list_files_full_path(IMAGES_DIR)

SOUND_FILE_NAMES_TO_FILES = {path.basename(file): file for file in SOUND_FILES}
MUSIC_FILE_NAMES_TO_FILES = {path.basename(file): file for file in MUSIC_FILES}
IMAGE_FILE_NAMES_TO_FILES = {path.basename(file): file for file in IMAGE_FILES}

Color = namedtuple('Color', ['name', 'value', 'value_range'])

COLORS = [
    Color('Cyan', (0, 255, 255), (numpy.array([0, 240, 240],numpy.uint8),numpy.array([15, 255, 255],numpy.uint8))),
    Color('Red', (255, 0, 0), (numpy.array([160, 160, 60],numpy.uint8),numpy.array([180, 255, 255],numpy.uint8))),
    Color('Green', (0, 255, 0), (numpy.array([38, 140, 60],numpy.uint8), numpy.array([75, 255, 255],numpy.uint8))),
    Color('Blue', (0, 0, 255), (numpy.array([75, 80, 80],numpy.uint8), numpy.array([130, 255, 255],numpy.uint8))),
    Color('Yellow', (255, 255, 0), (numpy.array([20, 100, 100],numpy.uint8), numpy.array([38, 255, 255],numpy.uint8))),
]

IDS = ['1337' for color in COLORS]
COMPORTS = ['COM10']

TRAIL_WIDTH = 3 * 2
PLAYER_RADIUS = 7
PLAYER_DIAMETER = PLAYER_RADIUS * 2

GAME_WIDTH = 500
GAME_HIGHT = 500

FPS_LIMIT = 100

TIME_TO_HOLE_MIN = 1.25 * 1000
TIME_TO_HOLE_MAX = 1.75 * 1000
HOLE_LENGTH = PLAYER_DIAMETER * 2


SCORE_CAP_MULTIPLIER = 5

BACKGROUND_MUSIC_VOLUME_LOW = 0.3
BACKGROUND_MUSIC_VOLUME_NORMAL = 0.9


MAX_WHEEL_SPEED = 255
MIN_WHEEL_SPEED = 0

TURN_WHEEL_SPEED_DIFFERENCE = 32

MAX_ROBOT_SPEED = MAX_WHEEL_SPEED - TURN_WHEEL_SPEED_DIFFERENCE
MIN_ROBOT_SPEED = MIN_WHEEL_SPEED + TURN_WHEEL_SPEED_DIFFERENCE

DEFAULT_ROBOT_SPEED = 128

# Debug speeds
if DEBUG:
    ROTATION_SPEED = 180 # Degrees per second
    DEFAULT_MOVEMENT_SPEED = 120 # pixels per second
    MAX_MOVEMENT_SPEED = 400
    MIN_MOVEMENT_SPEED = 30

SPEED_MODIFICATION_RATIO = 0.50

TRAIL_NON_COLLIDING_LAST_POINTS = 60

CLEAR_COLOR = (0, 0, 0, 0)

MENU_BACKGROUND_COLOR = (51, 51, 51)

GAME_BACKGROUNG_COLOR = (0, 0, 0)

BONUS_SIZE = 35
BONUS_DIMENSIONS = (BONUS_SIZE, BONUS_SIZE)

TIME_TO_BONUS_MIN = 3 * 1000
TIME_TO_BONUS_MAX = 10 * 1000
if DEBUG_BONUSES:
    TIME_TO_BONUS_MIN = 1 * 1000
    TIME_TO_BONUS_MAX = 2 * 1000

# Menu constants
NO_OPTION = -1

#
# Classes
#

class RobotNotFoundError(Exception):
    pass

class Bonus(object):
    """Abstart base class for bonuses"""
    surface = None
    DURATION_MIN = None
    DURATION_MAX = None

    def __init__(self, game, position):
        self.game = game
        self.position = position
        self.duration = random.uniform(self.DURATION_MIN, self.DURATION_MAX)

    def activate(self, picker):
        self.picker = picker

    def deactivate(self):
        pass

    def draw(self):
        self.game.surface.blit(self.surface, self.position)

    def get_rect(self):
        return self.surface.get_rect(topleft=self.position)

def load_bonus_image(image_file_name):
    file_path = IMAGE_FILE_NAMES_TO_FILES[image_file_name]
    surface = pygame.image.load(file_path)
    scaled_surface = pygame.transform.smoothscale(surface, BONUS_DIMENSIONS)
    return scaled_surface

class ModifySelfSpeed(Bonus):
    ROBOT_SPEED_DELTA = None
    MOVEMENT_SPEED_DELTA = None

    def activate(self, picker):
        super(ModifySelfSpeed, self).activate(picker)

        self.robot_speed_delta = self.ROBOT_SPEED_DELTA
        self.movement_speed_delta = self.MOVEMENT_SPEED_DELTA

        self.robot_speed_delta, self.movement_speed_delta = picker.modifySpeedBounded(self.robot_speed_delta, self.movement_speed_delta)

    def deactivate(self):
        self.picker.modifySpeedBounded(-self.robot_speed_delta, -self.movement_speed_delta)

class SpeedUpSelf(ModifySelfSpeed):
    surface = load_bonus_image('SpeedUp.png')
    DURATION_MIN = 1 * 1000
    DURATION_MAX = 3 * 1000
    ROBOT_SPEED_DELTA = DEFAULT_ROBOT_SPEED * SPEED_MODIFICATION_RATIO
    MOVEMENT_SPEED_DELTA = DEFAULT_MOVEMENT_SPEED * SPEED_MODIFICATION_RATIO

class SpeedDownSelf(ModifySelfSpeed):
    surface = load_bonus_image('SpeedDown.png')
    DURATION_MIN = 1 * 1000
    DURATION_MAX = 3 * 1000
    ROBOT_SPEED_DELTA = -(DEFAULT_ROBOT_SPEED * SPEED_MODIFICATION_RATIO)
    MOVEMENT_SPEED_DELTA = -(DEFAULT_MOVEMENT_SPEED * SPEED_MODIFICATION_RATIO)

##class SpeedUpOthers(Bonus):
##    surface = None #TODO
##    DURATION_MIN = 1 * 1000
##    DURATION_MAX = 3 * 1000
##
##    def activate(self, picker):
##        super(SpeedUpOthers, self).activate(picker)
##        others = [p for p in self.game.players_alive if p != picker]
##        for player in others:
##            player.increaseSpeed()

##class SpeedDownOthers(Bonus):
##    surface = None #TODO
##    DURATION_MIN = 1 * 1000
##    DURATION_MAX = 3 * 1000
##
##    def activate(self, picker):
##        super(SpeedDownOthers, self).activate(picker)
##        others = [p for p in self.game.players_alive if p != picker]
##        for player in others:
##            player.decreaseSpeed()

# TODO: make Game choose random bonuses from these
#BONUSES = [SpeedUpSelf, SpeedUpOthers, SpeedDownSelf, SpeedDownOthers]
BONUSES = [SpeedUpSelf, SpeedDownSelf]

class Trail:
    def __init__(self, game_surface, color):
        self.game_surface = game_surface
        self.surface = pygame.Surface((GAME_WIDTH, GAME_HIGHT), flags=pygame.SRCALPHA)
        self.color = color
        self.last_points = []
        self.self_collision_surface = pygame.Surface((GAME_WIDTH, GAME_HIGHT), flags=pygame.SRCALPHA)

    def reset(self):
        self.last_points = []
        self.self_collision_surface.fill(CLEAR_COLOR)
        self.surface.fill(CLEAR_COLOR)

    def addPoint(self, point):
        int_point = (int(round(point.x)), int(round(point.y)))
        pygame.draw.circle(self.surface, self.color.value, int_point, TRAIL_WIDTH / 2)

        self.last_points.append(int_point)
        if len(self.last_points) > TRAIL_NON_COLLIDING_LAST_POINTS:
            first_last_point = self.last_points.pop(0)
            self_collision_trail_color = (128, 0, 128) if DEBUG_TRAIL else self.color.value
            pygame.draw.circle(self.self_collision_surface, self_collision_trail_color, first_last_point, TRAIL_WIDTH / 2)

    def draw(self):
        self.game_surface.blit(self.surface, (0, 0))
        if DEBUG_TRAIL:
            self.game_surface.blit(self.self_collision_surface, (0, 0))

class RobotController(object):
    def __init__(self, arduino_controller):
        self.controller = arduino_controller
        self.speed = 0
        self.direction = STRAIGHT
        self.moving = False
        self.prev_speed = self.speed
        self.prev_direction = self.direction

    def go(self):
        self.controller.move()

    def stop(self):
        self.controller.stop()

    def updateRobotMovement(self):
        movement_changed = self.speed != self.prev_speed or self.direction != self.prev_direction
        if not movement_changed:
            return

        if self.direction == STRAIGHT:
            self.controller.setSpeedLeft(self.speed)
            self.controller.setSpeedRight(self.speed)
        elif self.direction == RIGHT:
            self.controller.setSpeedLeft(self.speed + TURN_WHEEL_SPEED_DIFFERENCE)
            self.controller.setSpeedRight(self.speed - TURN_WHEEL_SPEED_DIFFERENCE)
        elif self.direction == LEFT:
            self.controller.setSpeedLeft(self.speed - TURN_WHEEL_SPEED_DIFFERENCE)
            self.controller.setSpeedRight(self.speed + TURN_WHEEL_SPEED_DIFFERENCE)
        else:
            assert False

        self.prev_speed = self.speed
        self.prev_direction = self.direction


class Player:
    def __init__(self, game_surface, color, controller):
        self.game_surface = game_surface
        self.surface = pygame.Surface((PLAYER_DIAMETER, PLAYER_DIAMETER), flags=pygame.SRCALPHA)
        self.color = color
        self.lowerColor = color.value_range[0]
        self.upperColor = color.value_range[1]
        self.alive = True
        self.direction = None
        self.position = None
        self.last_position = None
        self.surface_position = None
        self.robot_speed = 0
        self.movement_speed = 0
        self.trail = Trail(self.game_surface, color)
        self.controller = controller

        self.time_to_next_hole = 0
        self.hole_length_remaining = 0
        self.creating_hole = False
        self.resetTimeToNextHole()
        self.score = 0
        if DEBUG_ROBOT:
            ser = serial.Serial('COM4', baudrate=38400)
            arduino = ArduinoController(ser, '1111')
            self.robot_controller = RobotController(arduino)

    def reset(self):
        self.alive = True
        self.trail.reset()
        self.creating_hole = False
        self.stop()
        self.resetTimeToNextHole()

    def go(self):
        self.setSpeed(DEFAULT_ROBOT_SPEED, DEFAULT_MOVEMENT_SPEED)

    def stop(self):
        self.setSpeed(0)
        if not DEBUG_WITHOUT_ROBOT:
            self.robot_controller.stop()

    def setSpeed(self, robot_speed, movement_speed=0):
        self.robot_speed = robot_speed
        if not DEBUG_WITHOUT_ROBOT:
            self.robot_controller.speed = robot_speed
        if DEBUG:
            self.movement_speed = movement_speed

    def modifySpeed(self, robot_speed_delta, movement_speed_delta=0):
        self.setSpeed(self.robot_speed + robot_speed_delta, self.movement_speed + movement_speed_delta)

    def modifySpeedBounded(self, robot_speed_delta, movement_speed_delta=0):
        if self.robot_speed + robot_speed_delta > MAX_ROBOT_SPEED:
            robot_speed_delta = MAX_ROBOT_SPEED - self.robot_speed
        if self.robot_speed + robot_speed_delta < MIN_ROBOT_SPEED:
            robot_speed_delta = -(self.robot_speed - MIN_ROBOT_SPEED)

        if DEBUG:
            if self.movement_speed + movement_speed_delta > MAX_MOVEMENT_SPEED:
                movement_speed_delta = MAX_MOVEMENT_SPEED - self.movement_speed
            if self.movement_speed + movement_speed_delta < MIN_MOVEMENT_SPEED:
                movement_speed_delta = -(self.movement_speed - MIN_MOVEMENT_SPEED)

        self.modifySpeed(robot_speed_delta, movement_speed_delta)
        return robot_speed_delta, movement_speed_delta

    def _set_position_and_direction_vector(self, position, direction_vector):
        self.position = position
        self.direction_vector = direction_vector

    def resetTimeToNextHole(self):
        self.time_to_next_hole = random.uniform(TIME_TO_HOLE_MIN, TIME_TO_HOLE_MAX)

    def tick(self, tick_duration):
        self.tick_duration = tick_duration

        if DEBUG:
            self._move()

        if not self.creating_hole:
            self.time_to_next_hole -= tick_duration
            if self.time_to_next_hole <= 0:
                self.creating_hole = True
                self.hole_length_remaining = HOLE_LENGTH

    def _move(self):
        assert DEBUG
        tick_duration_seconds = self.tick_duration / 1000.0
        rotation = ROTATION_SPEED * tick_duration_seconds
        movement = self.movement_speed * tick_duration_seconds

        if self.direction == LEFT:
            self.direction_vector.rotate(-rotation)
        elif self.direction == RIGHT:
            self.direction_vector.rotate(rotation)

        self.position += (self.direction_vector * movement)

    def draw(self):
        self.game_surface.blit(self.surface, self.surface_position)

    def getRobotPositionFromCamera(self):
        """Get Position from camera via opencv. Throw RobotNotFoundError if robot not found."""
        if DEBUG:
            return self.position

        elif DEBUG_WEBCAM:
            maxArea = 0
            maxCnt = []
            maxPosX = 0
            maxPosY = 0
            ret, frame = webcam.webCamCapture.read() # ret value true if capture from webCam went good, frame is the picture from the webCam
            if ret == True:
                newFrame = Webcam.fixCap(frame)
                if DEUBG_WEBCAM_WITH_WINDOW:
                    cv2.imshow("WebCam", newFrame)
                img = cv2.GaussianBlur(newFrame, (5,5), 0)
                img = cv2.cvtColor(newFrame, cv2.COLOR_BGR2HSV)
                binaryColor = cv2.inRange(img, self.lowerColor, self.upperColor) # #creating a threshold image that contains pixels in between color Upper and Lower
                contours, hier = cv2.findContours(binaryColor, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    for cnt in contours:
                        moments = cv2.moments(cnt)
                        area = moments['m00']
                        approx = cv2.approxPolyDP(cnt,0.05*cv2.arcLength(cnt,True),True)
                        if len(approx) == 3:
                            if area > maxArea:
                                maxArea = area
                                maxCnt = cnt
                                maxPosX = int(moments['m10'] / area)
                                maxPosY = int(moments['m01'] / area)
                    self.position = (maxPosX, maxPosY)
                if maxArea == 0:
                    raise RobotNotFoundError()

    def updatePosition(self, add_to_trail=False):
        self.position = Vec2d(self.getRobotPositionFromCamera())
        self.surface_position = (int(self.position.x - PLAYER_RADIUS), int(self.position.y - PLAYER_RADIUS))
        self.surface.fill(CLEAR_COLOR)
        pygame.draw.circle(self.surface, self.color.value, (PLAYER_RADIUS, PLAYER_RADIUS), PLAYER_RADIUS)

        if self.creating_hole and self.last_position is not None:
            delta = self.position - self.last_position
            distance = delta.get_length()
            self.hole_length_remaining -= distance
            if self.hole_length_remaining <= 0:
                self.creating_hole = False
                self.resetTimeToNextHole()

        if add_to_trail and not self.creating_hole:
            self.trail.addPoint(Vec2d(self.position))

        self.last_position = Vec2d(self.position)

    def updateDirection(self):
        self.direction = self.controller.getDirection()
        if not DEBUG_WITHOUT_ROBOT:
            self.robot_controller.direction = self.direction

    def die(self):
        self.alive = False
        self.stop()
        self.electrify()

    def electrify(self):
        """Shock player with electric pulse"""
        pass

class Screen:
    def __init__(self):
        flags = 0
        if FULLSCREEN:
            flags |= pygame.FULLSCREEN
        self.surface = pygame.display.set_mode((GAME_WIDTH, GAME_HIGHT), flags)

        if FULLSCREEN:
            # It takes some time for the screen to adjust,
            # so wait to let the program resume when the screen is ready.
            pygame.time.wait(2000)

class EscapeException(Exception):
    pass

class Game:
    def __init__(self, game_screen):
        self.surface = game_screen.surface

        self.music_file = random.choice(MUSIC_FILES)

        self.clock = pygame.time.Clock()

        self.begin_sound = pygame.mixer.Sound(SOUND_FILE_NAMES_TO_FILES['begin.wav'])
        self.start_beeps_sound = pygame.mixer.Sound(SOUND_FILE_NAMES_TO_FILES['start_beeps.wav'])
        self.explosion_sound = pygame.mixer.Sound(SOUND_FILE_NAMES_TO_FILES['80938__tony-b-kksm__soft-explosion.wav'])

        self.controllers = getControllers(PLAYERS_COUNT)

        self.players = [Player(self.surface, color, controller) for color, controller in zip(COLORS, self.controllers)]
        self.players_alive = self.players[:]

        menu_options = [('Play (Set controls first)',self.play_game), ('Set Controls',None), ('Debug Options',None), ('Quit',exit_)]
        self.menu = MenuWrapper(self.surface, self.clock)
        for option, function in menu_options:
            self.menu.addOption(option, function)

    def _randomize_players_positions_and_direction_vectors(self):
        for player in self.players:
            MARGIN_FACTOR = 5
            WIDTH_MARGIN = GAME_WIDTH / MARGIN_FACTOR
            HIGHT_MARGIN = GAME_HIGHT / MARGIN_FACTOR
            x = random.randrange(WIDTH_MARGIN, GAME_WIDTH - WIDTH_MARGIN)
            y = random.randrange(HIGHT_MARGIN, GAME_HIGHT - HIGHT_MARGIN)
            direction_vector = Vec2d(1, 0)
            direction_vector.rotate(random.randrange(0, 360))
            player._set_position_and_direction_vector(Vec2d(x, y), direction_vector)

    def kill_player(self, player):
        player.die()
        self.explosion_sound.play()
        self.players_alive.remove(player)
        for player in self.players_alive:
            player.score += 1

    def handle_events(self): # Note: Removed to work nicely with the new menu
        events = list(pygame.event.get())
        return events

    def handle_events(self):
        events = list(pygame.event.get())
        for event in events:
            if event.type == pygame.QUIT:
                exit_()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.escape()
        return events

    def start(self):
        while True:
            try:
                self.menu.showMenu()
            except EscapeException:
                pass

    def escape(self):
        raise EscapeException()

    def play_game(self):
        score_cap = max(len(self.players) - 1, 1) * SCORE_CAP_MULTIPLIER

        pygame.mixer.music.load(self.music_file)
        pygame.mixer.music.set_volume(BACKGROUND_MUSIC_VOLUME_LOW)
        pygame.mixer.music.play(-1)

        if DEBUG_SINGLE_PLAYER:
            round_count = 2

        while True:
            self.play_round()

            winners = [p for p in self.players if p.score >= score_cap]
            if len(winners) > 0:
                winner = None
                if len(winners) == 1:
                    winner = winners[0]
                else:
                    # more the one player reached score cap
                    winners.sort(key = lambda player: player.score)
                    if winners[0] > winners[1]:
                        winner = winners[0]
                    else:
                        # play another round, until there is a final winner
                        pass
                if winner is not None:
                    print 'The winner is %s!' % winner.color.name
                    break

            if DEBUG_SINGLE_PLAYER:
                round_count -= 1
                if round_count == 0:
                    break

    def play_round(self):
        for player in self.players:
            player.reset()
        self.players_alive = self.players[:]

        if DEBUG:
            self._randomize_players_positions_and_direction_vectors()

        self.pre_round_wait()
        self.pre_round_start()
        self.do_play_round()

        #TODO: replace with HUD updates
        for player in self.players:
            print ''
            print '%s: %d' % (player.color.name, player.score)

    def pre_round_wait(self):
        while True:
            events = self.handle_events()

            self.clearSurface()
            for player in self.players:
                player.updatePosition()
                player.draw()
            self.updateDisplay()

            for event in events:
               if event.type == pygame.KEYDOWN and event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    return True

            self.tick()

    def pre_round_start(self):
        sound_length = self.start_beeps_sound.get_length()
        current_time = pygame.time.get_ticks()
        sound_end_time = current_time + int(sound_length * 1000)
        self.start_beeps_sound.play()
        while True:
            try:
                self.handle_events()
            except EscapeException:
                self.start_beeps_sound.stop()
                raise
            # TODO: display on the Screen 3, 2, 1, Begin!
            if pygame.time.get_ticks() >= sound_end_time:
                break
            self.tick()

    def do_play_round(self):
        paused = False

        self.begin_sound.play()
        pygame.mixer.music.set_volume(BACKGROUND_MUSIC_VOLUME_NORMAL)

        bonuses = []
        activated_bonuses = []
        next_bonus_time = self.get_randomized_next_bonus_time()

        for player in self.players:
            player.go()

        while True:
            tick_duration = self.tick()
            events = self.handle_events()
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        paused = not paused
                        #TODO: start/stop robots

            if not paused:
                for player in self.players_alive[:]:
                    try:
                        player.tick(tick_duration)
                        player.updatePosition(add_to_trail=True)
                        player.updateDirection()
                    except RobotNotFoundError:
                        self.kill_player(player)

                next_bonus_time -= tick_duration
                if next_bonus_time <= 0:
                    bonus = self.get_randomized_bonus()
                    bonuses.append(bonus)
                    next_bonus_time = self.get_randomized_next_bonus_time()

                for player in self.players_alive:
                    if not DEBUG_WITHOUT_ROBOT:
                        player.robot_controller.updateRobotMovement()

                self.clearSurface()
                for player in self.players:
                    player.trail.draw()
                    player.draw()
                for bonus in bonuses:
                    bonus.draw()
                self.updateDisplay()

                for player in self.players_alive[:]:
                    for bonus in activated_bonuses:
                        bonus.duration -= tick_duration
                        if bonus.duration <= 0:
                            bonus.deactivate()
                            activated_bonuses.remove(bonus)

                    for bonus in bonuses:
                        if self.playerCollidesWithBonus(player, bonus):
                            bonus.activate(player)
                            bonuses.remove(bonus)
                            activated_bonuses.append(bonus)

                    if self.playerCollidesWithWalls(player):
                        self.kill_player(player)

                    if self.playerCollidesWithItself(player):
                        self.kill_player(player)

                    # Check other players' trails
                    for trail in (p.trail for p in self.players if p != player):
                        if self.playerCollidesWithTrail(player, trail):
                            self.kill_player(player)

                # Check end conditions
                if len(self.players_alive) <= 1:
                    if not (DEBUG_SINGLE_PLAYER and len(self.players_alive) == 1):
                        break

        pygame.mixer.music.set_volume(BACKGROUND_MUSIC_VOLUME_LOW)

    def get_randomized_next_bonus_time(self):
        next_bonus_time = random.uniform(TIME_TO_BONUS_MIN, TIME_TO_BONUS_MAX)
        return next_bonus_time

    def get_randomized_bonus(self):
        bonus_class = random.choice(BONUSES)
        bonus_w = bonus_class.surface.get_width()
        bonus_h = bonus_class.surface.get_height()
        x = random.randrange(0, GAME_WIDTH - bonus_w)
        y = random.randrange(0, GAME_WIDTH - bonus_h)
        bonus = bonus_class(self, (x, y))
        return bonus

    def clearSurface(self):
        self.surface.fill(GAME_BACKGROUNG_COLOR)

    def updateDisplay(self):
        pygame.display.flip()

    def playerCollidesWithBonus(self, player, bonus):
        bonus_mask = pygame.mask.from_surface(bonus.surface)
        player_mask = pygame.mask.from_surface(player.surface)

        bonus_offset = Vec2d(bonus.position) - Vec2d(player.surface_position)

        overlap_point = player_mask.overlap(bonus_mask, bonus_offset)
        if overlap_point is None:
            return False
        else:
            return True

    def playerCollidesWithWalls(self, player):
        x, y = player.position
        left_wall_collision = x - PLAYER_RADIUS < 0
        top_wall_collision = y - PLAYER_RADIUS < 0
        right_wall_collision = x + PLAYER_RADIUS > GAME_WIDTH
        bottom_wall_collision = y + PLAYER_RADIUS > GAME_HIGHT
        any_wall_collision = left_wall_collision or top_wall_collision or right_wall_collision or bottom_wall_collision
        return any_wall_collision

    def playerCollidesWithItself(self, player):
        player_mask = pygame.mask.from_surface(player.surface)
        trail_mask = pygame.mask.from_surface(player.trail.self_collision_surface)

        overlap_point = trail_mask.overlap(player_mask, player.surface_position)
        if overlap_point is None:
            return False
        else:
            return True

    def playerCollidesWithTrail(self, player, trail):
        player_mask = pygame.mask.from_surface(player.surface)
        trail_mask = pygame.mask.from_surface(trail.surface)

        overlap_point = trail_mask.overlap(player_mask, player.surface_position)
        if overlap_point is None:
            return False
        else:
            return True

    def tick(self):
        """Wait for the next game tick"""
        tick_duration = self.clock.tick(FPS_LIMIT)
        current_fps = self.clock.get_fps()
        pygame.display.set_caption("FPS: %f" % current_fps)
        return tick_duration

class MenuWrapper():
    def __init__(self, screen, clock, music_file = r'music\Menu music\MenuMusic - Threshold 8 bit.ogg'):
        self.screen = screen
        self.clock = clock
        self.options = []
        self.functions = []
        self.music_file = music_file

    def addOption(self, caption, function = None):
        self.options.append(caption)
        self.functions.append(function)

    def showMenu(self):
        if [] == self.options: # If there are no menu items, return NO_OPTION
            return NO_OPTION

        # Start menu music!
        pygame.mixer.music.load(self.music_file)
        pygame.mixer.music.set_volume(BACKGROUND_MUSIC_VOLUME_LOW)
        pygame.mixer.music.play(-1)

        self.screen.fill(MENU_BACKGROUND_COLOR)

        current_menu = menu.Menu()
        current_menu.init(self.options, self.screen)
        current_menu.draw()

        pygame.display.update()
        while True:
            finished = False
            for event in pygame.event.get():
                if event.type == pygame.locals.KEYDOWN:
                    if event.key == pygame.locals.K_UP:
                        current_menu.draw(-1)
                    elif event.key == pygame.locals.K_DOWN:
                        current_menu.draw(1)
                    elif event.key in [pygame.locals.K_RETURN, pygame.K_KP_ENTER]:
                        selection = current_menu.get_position()
                        if None != self.functions[selection]:
                            self.functions[selection]()
                            finished = True
                            break
                    elif event.key == pygame.locals.K_ESCAPE:
                        exit_()
                    pygame.display.update()
                elif event.type == pygame.locals.QUIT:
                    exit_()
            if finished:
                break
            self.clock.tick(FPS_LIMIT)
            current_fps = self.clock.get_fps()
            pygame.display.set_caption("FPS: %f" % current_fps)

def main():
    global webcam
    if DEBUG_WEBCAM:
        webcam = WebCam()
    game_screen = Screen()
    game = Game(game_screen)
    game.start()
    exit_()

if "__main__" == __name__:
    main()
