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
import pdb

from Controllers import *

if USE_WEBCAM:
    import cv2
    import cv2.cv as cv

##
## TODO:
##     - Add more bonuses (speed up/down, control reverse, players swap, electrify etc...)
##     - In pre_round stage, enable robot control for manual robot positioning
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
FONTS_DIR = path.join(ROOT_DIR, 'Fonts')

def list_files_full_path(directory):
    entries = [path.join(directory, entry) for entry in os.listdir(directory)]
    files = [entry for entry in entries if path.isfile(entry)]
    return files

SOUND_FILES = list_files_full_path(SOUND_DIR)
MUSIC_FILES = list_files_full_path(MUSIC_DIR)
IMAGE_FILES = list_files_full_path(IMAGES_DIR)
FONT_FILES = list_files_full_path(FONTS_DIR)

SOUND_FILE_NAMES_TO_FILES = {path.basename(file): file for file in SOUND_FILES}
MUSIC_FILE_NAMES_TO_FILES = {path.basename(file): file for file in MUSIC_FILES}
IMAGE_FILE_NAMES_TO_FILES = {path.basename(file): file for file in IMAGE_FILES}
FONT_FILE_NAMES_TO_FILES = {path.basename(file): file for file in FONT_FILES}

Color = namedtuple('Color', ['name', 'value', 'value_range'])

COLORS = [
    Color('Cyan', (0, 255, 255), (numpy.array([0, 240, 240],numpy.uint8),numpy.array([15, 255, 255],numpy.uint8))),
    Color('Red', (255, 0, 0), (numpy.array([121, 107, 107],numpy.uint8), numpy.array([180, 178, 187],numpy.uint8))),
    Color('Green', (0, 255, 0), (numpy.array([67, 78, 72],numpy.uint8), numpy.array([116, 166, 106],numpy.uint8))),
    Color('Blue', (0, 0, 255), (numpy.array([110, 135, 109],numpy.uint8), numpy.array([130, 197, 155],numpy.uint8))),
    Color('Yellow', (255, 255, 0),(numpy.array([25, 99, 159],numpy.uint8), numpy.array([35, 180, 206],numpy.uint8)))]


IDS = ['1337' for color in COLORS]
COMPORTS = ['COM10']

TRAIL_WIDTH = 1
PLAYER_RADIUS = 7
PLAYER_DIAMETER = PLAYER_RADIUS * 2
PLAYER_BORDER_WIDTH = 1

GAME_WIDTH = 500
GAME_HIGHT = 500

GAME_BORDER_WIDTH = 10
GAME_BORDER_COLOR = (255, 255, 255)

GUI_MARGIN = 150
TITLE_MARGIN = 75
SCORES_MARGIN_BOTTOM = 15

SCREEN_WIDTH = GAME_WIDTH + GAME_BORDER_WIDTH * 2
SCREEN_HIGHT = GAME_HIGHT + GAME_BORDER_WIDTH * 2 + GUI_MARGIN

SEARCH_RADIUS = (GAME_WIDTH / 2) - 1

WEBCAM_NUMBER = 2 #default webcam is 0

ROBOT_NOT_FOUND_LIMIT = 20
RECTANGLE_NOT_FOUND_LIMIT = 50
NUMBER_OF_FRAMES_BETWEEN_BORDERS_SEARCH = 5000
MINIMUM_BORDER_SIZE = 1000

FPS_LIMIT = 100

TIME_TO_HOLE_MIN = 1.25 * 1000
TIME_TO_HOLE_MAX = 1.75 * 1000
HOLE_LENGTH = PLAYER_DIAMETER * 2

SCORE_CAP_MULTIPLIER = 5

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

NON_COLLIDING_TRAIL_MAX_LENGTH = PLAYER_DIAMETER * 2

CLEAR_COLOR = (0, 0, 0, 0)

GAME_BACKGROUNG_COLOR = (0, 0, 0)
GUI_BACKGROUND_COLOR = (51, 51, 51)
TITLE_COLOR = (255, 91, 49)
WINNING_ANNOUNCEMENT_BOX_COLOR = (50, 50, 50, 200)
WINNING_ANNOUNCEMENT_BOX_BORDER_COLOR = (150, 150, 150)
WINNING_ANNOUNCEMENT_BOX_BORDER_WIDTH = 5

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

class gamesBordersNotFound(Exception):
    #TODO create warning that no game borders detected
    pass

class webcamNotWorking(Exception):
    # webcam is not working properly
    pass

class RobotNotFoundError(Exception):
    #TODO remove robot from playing robots list
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
        self.game.game_surface.blit(self.surface, self.position)

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
        self.last_point = None
        self.last_points = []
        self.non_colliding_trail_length = 0
        self.self_collision_surface = pygame.Surface((GAME_WIDTH, GAME_HIGHT), flags=pygame.SRCALPHA)

    def reset(self):
        self.last_point = None
        self.last_points = []
        self.non_colliding_trail_length = 0
        self.self_collision_surface.fill(CLEAR_COLOR)
        self.surface.fill(CLEAR_COLOR)

    def addPoint(self, point, is_hole=False, distance_from_last_point=0):
        int_point = (int(round(point.x)), int(round(point.y)))
        if not is_hole and self.last_point is not None:
            pygame.draw.line(self.surface, self.color.value, self.last_point, int_point, TRAIL_WIDTH)

        self.last_point = int_point
        self.last_points.append((int_point, is_hole, distance_from_last_point))

        self.non_colliding_trail_length += distance_from_last_point
        while self.non_colliding_trail_length > NON_COLLIDING_TRAIL_MAX_LENGTH:
            first_last_point, is_hole, distance = self.last_points.pop(0)
            second_last_point, _, _ = self.last_points[0]
            self.non_colliding_trail_length -= distance
            self_collision_trail_color = (128, 0, 128) if DEBUG_TRAIL else self.color.value
            if not is_hole:
                pygame.draw.line(self.self_collision_surface, self_collision_trail_color, first_last_point, second_last_point, TRAIL_WIDTH)

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

class WebCam(object):
    def __init__(self):
        self.approx = []
        self.webCamCapture = cv2.VideoCapture(WEBCAM_NUMBER)
        self.size =  numpy.array([ [0,0],[GAME_WIDTH,0],[GAME_WIDTH, GAME_HIGHT],[0,GAME_HIGHT] ],numpy.float32)
        self.framesCounter = 0
        self.frame = None
        self.numberOfFramesBetweenEachCheck = NUMBER_OF_FRAMES_BETWEEN_BORDERS_SEARCH
        self.dontStartUntilBorderIsFound()

    def takePicture(self):
        ret, frame = self.webCamCapture.read()
        if ret:
            self.frame = frame
        else:
            raise webCamFailure()


    def dontStartUntilBorderIsFound(self):
        """don't start game until game's frame is found, trying RECTANGLE_NOT_FOUND_LIMIT times"""
        retriesCounter = 0
        while self.approx == []:
            self.takePicture()
            self.approx = self.findBorder(self.frame)
            if self.approx == []:
                retriesCounter += 1
            if retriesCounter == RECTANGLE_NOT_FOUND_LIMIT:
                raise gamesBordersNotFound()

    def findPlayer(self, player):
        """if frames counter is multiple of NUMBER_OF_FRAMES_BETWEEN_RECTANGLE_SEARCH find game's borders. change frame to fit borders. find playing players in fixed frame"""
        if self.framesCounter % self.numberOfFramesBetweenEachCheck == 0:
            self.findBorder(self.frame)
            self.framesCounter = 0

        rectFrame = self.frameToBorder(self.frame)
        if DEUBG_WEBCAM_WITH_WINDOW:
            cv2.imshow('Webcam capture', rectFrame)
            cv2.waitKey(1)

        position = self.findRobot(rectFrame, player)
        self.framesCounter += 1
        return position

    def findBorder(self, frame):
        """find game's borders"""
        maxContourArea = MINIMUM_BORDER_SIZE #minimum borders size
        maxCnt = 0
        maxApprox = 0

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255,1,1,11,2)
        contours, hier = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            for cnt in contours:
                cntArea = cv2.contourArea(cnt)
                peri = cv2.arcLength(cnt,True)
                approx = cv2.approxPolyDP(cnt, 0.02*peri, True)
                if len(approx) == 4 and cntArea > maxContourArea:
                    maxContourArea = cntArea
                    maxCnt = cnt
                    maxApprox = approx

            if maxContourArea != MINIMUM_BORDER_SIZE:
                return self.rectify(maxApprox) # if no frame found -> stay with last borders

    def frameToBorder(self, frame):
        """transform frame to fit to borders"""
        retval = cv2.getPerspectiveTransform(self.approx, self.size)
        warp = cv2.warpPerspective(frame,retval,(GAME_WIDTH, GAME_HIGHT))
        return warp

    def findRobot(self, frame, player):
        """finds all playing robots"""
        erodeKernel = numpy.ones((5,5),numpy.uint8)
        dilateKernel = numpy.ones((6,6),numpy.uint8)
        maxArea = 0
        maxCnt = []
        maxPosx = 0
        maxPosy = 0
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        binaryColor = cv2.inRange(img, player.lowerColor, player.upperColor)
        erosion = cv2.erode(binaryColor, erodeKernel, iterations = 1) #noise removal
        dilation = cv2.dilate(erosion, dilateKernel, iterations = 2) #opposite noise removal
        croppedBinary, maxBinaryX, maxBinaryY  = self.croper(player, dilation)
        contours, hier = cv2.findContours(croppedBinary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            for cnt in contours:
                approx = cv2.approxPolyDP(cnt,0.1*cv2.arcLength(cnt,True),True)
                if len(approx) == 3:
                    moments = cv2.moments(cnt)
                    area = moments['m00']
                    if area > maxArea:
                        maxArea = area
                        maxCnt = cnt
                        maxPosx = int(moments['m10'] / area) + maxBinaryX
                        maxPosy = int(moments['m01'] / area) + maxBinaryY

            if maxArea > 0:
                player.position = Vec2d(maxPosx, maxPosy)
                player.notFoundCounter = 0
                player.updatePlayerRadius()
            else:
                player.notFound()
        else:
            player.notFound()
        return player.position


    @staticmethod
    def rectify(h):
        """this function put vertices of square of the board, in clockwise order"""
        h = h.reshape((4,2))
        hnew = numpy.zeros((4,2),dtype = numpy.float32)

        add = h.sum(1)
        hnew[0] = h[numpy.argmin(add)]
        hnew[2] = h[numpy.argmax(add)]

        diff = numpy.diff(h,axis = 1)
        hnew[1] = h[numpy.argmin(diff)]
        hnew[3] = h[numpy.argmax(diff)]

        return hnew

    @staticmethod
    def croper(player, frame):
        """crop frame to radius around last player position """
        if player.position.x - player.radius <= 0 and player.position.x + player.radius <= GAME_WIDTH:
            topX = 0
            bottomX = player.position.x + player.radius
        elif player.position.x - player.radius >= 0 and player.position.x + player.radius <= GAME_WIDTH:
            topX = player.position.x - player.radius
            bottomX = player.position.x + player.radius
        elif player.position.x - player.radius >= 0 and player.position.x + player.radius >= GAME_WIDTH:
            topX = player.position.x - player.radius
            bottomX = GAME_WIDTH
        else:
            print "WTF?! player.position.y: %d player.position.x: %d" % (player.position.y, player.position.x)

        if player.position.y - player.radius <= 0 and player.position.y + player.radius <= GAME_HIGHT:
            topY = 0
            bottomY = player.position.y + player.radius
        elif player.position.y - player.radius >= 0 and player.position.y + player.radius <= GAME_HIGHT:
            topY = player.position.y - player.radius
            bottomY = player.position.y + player.radius
        elif player.position.y - player.radius >= 0 and player.position.y + player.radius >= GAME_HIGHT:
            topY = player.position.y - player.radius
            bottomY = GAME_HIGHT
        else:
            print "WTF?! player.position.y: %d player.position.x: %d" % (player.position.y, player.position.x)

        cropedFrame = numpy.array(frame[topY:bottomY, topX:bottomX])
        return cropedFrame, topX, topY

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
        self.radius = SEARCH_RADIUS
        self.notFoundCounter = 0

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
        self.notFoundCounter = 0
        self.radius = SEARCH_RADIUS
        self.alive = True
        self.trail.reset()
        self.creating_hole = False
        self.last_position = None
        self.hole_length_remaining = 0
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

    def updatePosition(self, add_to_trail=False):
        if USE_WEBCAM:
            self.position = Vec2d(webcam.findPlayer(self))


        self.surface_position = (int(self.position.x - PLAYER_RADIUS), int(self.position.y - PLAYER_RADIUS))
        self.surface.fill(CLEAR_COLOR)
        pygame.draw.circle(self.surface, GAME_BACKGROUNG_COLOR, (PLAYER_RADIUS, PLAYER_RADIUS), PLAYER_RADIUS)
        pygame.draw.circle(self.surface, self.color.value, (PLAYER_RADIUS, PLAYER_RADIUS), PLAYER_RADIUS, PLAYER_BORDER_WIDTH)

        distance_from_last_point = 0
        if self.last_position is not None:
            delta = self.position - self.last_position
            distance_from_last_point = delta.get_length()
            if self.creating_hole:
                self.hole_length_remaining -= distance_from_last_point
                if self.hole_length_remaining <= 0:
                    self.creating_hole = False
                    self.resetTimeToNextHole()
                    distance_from_last_point = 0

        if add_to_trail:
            self.trail.addPoint(Vec2d(self.position), self.creating_hole, distance_from_last_point)


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

    def notFound(self):
        """if robot not found ROBOT_NOT_FOUND_LIMIT times raise robotNotFoundException"""
        if self.notFoundCounter == ROBOT_NOT_FOUND_LIMIT:
            raise RobotNotFoundError()
        else:
            self.notFoundCounter += 1

    def updatePlayerRadius(self):
        """change player radius after initialisation SHOULD BE CHANGED!! NOT GOOD!"""
        if self.radius == SEARCH_RADIUS:
            self.radius = 100

    def setController(self, controller):
        """Change the player's controller"""
        self.controller = controller

class MusicMixer:
    def __init__(self):
        self.background_music_volume_low = 0.3
        self.background_music_volume_normal = 0.9
        self.background_music_file = None
        pygame.mixer.music.set_volume(self.background_music_volume_low)

    def setBackgroundMusic(self, file):
        if self.background_music_file == file:
            return
        self.background_music_file = file
        self.playBackgroundMusic()

    def playBackgroundMusic(self):
        pygame.mixer.music.load(self.background_music_file)
        pygame.mixer.music.play(-1)

    def replayBackgroundMusic(self):
        pygame.mixer.music.play(-1)

    def setVolume(self, volume):
        pygame.mixer.music.set_volume(volume)

class Screen:
    def __init__(self):
        flags = 0
        if FULLSCREEN:
            flags |= pygame.FULLSCREEN
        self.surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HIGHT), flags)

        if FULLSCREEN:
            # It takes some time for the screen to adjust,
            # so wait to let the program resume when the screen is ready.
            pygame.time.wait(2000)

class EscapeException(Exception):
    pass

class Game:
    def __init__(self, game_screen, music_mixer):
        self.screen_surface =  game_screen.surface
        self.music_mixer = music_mixer
        self.game_surface = pygame.Surface((GAME_WIDTH, GAME_HIGHT), flags=pygame.SRCALPHA)

        self.music_file = random.choice(MUSIC_FILES)

        self.clock = pygame.time.Clock()

        self.begin_sound = pygame.mixer.Sound(SOUND_FILE_NAMES_TO_FILES['begin.wav'])
        self.start_beeps_sound = pygame.mixer.Sound(SOUND_FILE_NAMES_TO_FILES['start_beeps.wav'])
        self.explosion_sound = pygame.mixer.Sound(SOUND_FILE_NAMES_TO_FILES['80938__tony-b-kksm__soft-explosion.wav'])
        self.winner_sound = pygame.mixer.Sound(SOUND_FILE_NAMES_TO_FILES['winner.wav'])

        controllers = getDefaultControllers(PLAYERS_COUNT) # Note: changed this. removed self.controllers, which was unused. If it shall be used, a good version of it will be a "getControllers" method which dinamically updates the controllers.
        self.players = [Player(self.game_surface, color, controller) for color, controller in zip(COLORS, controllers)]
        self.players_alive = self.players[:]

        # Set menus

        self.main_menu = menu.MenuWrapper(self.screen_surface, self.clock, self.music_mixer)
        self.set_controls_menu = menu.MenuWrapper(self.screen_surface, self.clock, self.music_mixer, music_file = None)
        self.controllers_options_menu = menu.MenuWrapper(self.screen_surface, self.clock, self.music_mixer, music_file = None)

        main_menu_options = [('Play',self.play_game), ('Set Controls',self.set_controls_menu.showMenu), ('Debug Options',None), ('Quit',exit_)]
        set_controls_menu_options = [('Player ' + str(number+1) + ': ' + self.players[number].color.name + ' (' + controllers[number].getType() + ')', self.controllers_options_menu.showMenu) for number in range(len(self.players))] + [('Back', self.main_menu.showMenu)]
        #controllers_options_menu_options = [(controller.getType() + ' ' + controller.getAdditionalInfo(), self.players[self.set_controls_menu.current_selection].setController(controller)) for controller in getControllers()] + [('Back', self.set_controls_menu.showMenu)]
        controllers_options_menu_options = [(controller.getType() + ' ' + controller.getAdditionalInfo(), None) for controller in getControllers()] + [('Back', self.set_controls_menu.showMenu)]

        self.main_menu.setOptions(main_menu_options)
        self.set_controls_menu.setOptions(set_controls_menu_options)
        self.controllers_options_menu.setOptions(controllers_options_menu_options)

        self.main_menu.setExitFunction(exit_)
        self.set_controls_menu.setExitFunction(self.main_menu.showMenu)
        self.controllers_options_menu.setExitFunction(self.set_controls_menu.showMenu)

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
        if player.alive:
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
        currentFunction = self.main_menu.showMenu
        while True:
            try:
                currentFunction = currentFunction()
                if currentFunction == self.play_game:
                    currentFunction = self.main_menu.showMenu
                    self.play_game()
            except EscapeException:
                pass

    def escape(self):
        raise EscapeException()

    def play_game(self):
        score_cap = max(len(self.players) - 1, 1) * SCORE_CAP_MULTIPLIER

        self.music_mixer.setBackgroundMusic(self.music_file)

        if DEBUG_SINGLE_PLAYER:
            round_count = 2

        for player in self.players:
            player.score = 0

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
                    break

            if DEBUG_SINGLE_PLAYER:
                round_count -= 1
                if round_count == 0:
                    winner = self.players[0]
                    break

            self.post_round()

        self.announce_winner(winner)

    def play_round(self):
        for player in self.players:
            player.reset()
        self.players_alive = self.players[:]

        if DEBUG:
            self._randomize_players_positions_and_direction_vectors()

        self.pre_round_wait()
        self.pre_round_start()

        self.music_mixer.setVolume(self.music_mixer.background_music_volume_normal)
        try:
            self.do_play_round()
        finally:
            self.music_mixer.setVolume(self.music_mixer.background_music_volume_low)

    def pre_round_wait(self):
        while True:
            events = self.handle_events()

            self.clearSurface()
            if USE_WEBCAM:
                webcam.takePicture()
            for player in self.players:
                player.updatePosition()
                player.draw()
            self.drawBorders()
            self.drawGui()
            self.updateDisplay()

            for event in events:
               if event.type == pygame.KEYDOWN and event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    return

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
        bonuses = []
        activated_bonuses = []
        next_bonus_time = self.get_randomized_next_bonus_time()

        self.begin_sound.play()

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
                next_bonus_time -= tick_duration
                if next_bonus_time <= 0:
                    bonus = self.get_randomized_bonus()
                    bonuses.append(bonus)
                    next_bonus_time = self.get_randomized_next_bonus_time()

                for bonus in activated_bonuses:
                        bonus.duration -= tick_duration
                        if bonus.duration <= 0:
                            bonus.deactivate()
                            activated_bonuses.remove(bonus)

                if USE_WEBCAM:
                    webcam.takePicture()

                for player in self.players_alive[:]:
                    player.updateDirection()
                    if not DEBUG_WITHOUT_ROBOT:
                        player.robot_controller.updateRobotMovement()
                    player.tick(tick_duration)
                    try:
                        player.updatePosition(add_to_trail=True)
                    except RobotNotFoundError:
                        self.kill_player(player)

                    if self.playerCrashesIntoAnything(player):
                        self.kill_player(player)

                    for bonus in bonuses:
                        if self.playerCollidesWithBonus(player, bonus):
                            bonus.activate(player)
                            bonuses.remove(bonus)
                            activated_bonuses.append(bonus)

                self.clearSurface()
                for player in self.players:
                    player.trail.draw()
                    player.draw()
                for bonus in bonuses:
                    bonus.draw()
                self.drawBorders()
                self.drawGui()
                self.updateDisplay()

                # Check end conditions
                if len(self.players_alive) <= 1:
                    if not (DEBUG_SINGLE_PLAYER and len(self.players_alive) == 1):
                        break

    def post_round(self):
        while True:
            events = self.handle_events()
            for event in events:
               if event.type == pygame.KEYDOWN and event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    return

            self.tick()

    def announce_winner(self, player):
        font = pygame.font.Font(FONT_FILE_NAMES_TO_FILES['menu_font.ttf'], 60)
        text = '%s Wins!' % player.color.name
        text_surface = font.render(text, True, player.color.value)
        text_rect = text_surface.get_rect(center=(GAME_WIDTH / 2, (GAME_HIGHT / 2)))
        box_rect = text_rect.inflate((100, 100))
        self.game_surface.fill(WINNING_ANNOUNCEMENT_BOX_COLOR, rect=box_rect)
        pygame.draw.rect(self.game_surface, WINNING_ANNOUNCEMENT_BOX_BORDER_COLOR, box_rect, WINNING_ANNOUNCEMENT_BOX_BORDER_WIDTH)
        self.game_surface.blit(text_surface, text_rect)
        self.updateDisplay()

        self.winner_sound.play()

        while True:
            events = self.handle_events()
            for event in events:
               if event.type == pygame.KEYDOWN and event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    return

            self.tick()

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
        self.screen_surface.fill(GAME_BACKGROUNG_COLOR)
        self.game_surface.fill(GAME_BACKGROUNG_COLOR)

    def drawBorders(self):
        border_rectangle = pygame.Rect(0, GUI_MARGIN, SCREEN_WIDTH, SCREEN_HIGHT)
        #Note: A filled rectangle is drawn, but it's ok because the game board is drawn after it
        pygame.draw.rect(self.screen_surface, GAME_BORDER_COLOR, border_rectangle)

    def drawGui(self):
        gui_rect = (0, 0, SCREEN_WIDTH, GUI_MARGIN)
        self.screen_surface.fill(GUI_BACKGROUND_COLOR, gui_rect)
        self.drawTitle()
        self.drawScores()

    def drawTitle(self):
        font = pygame.font.Font(FONT_FILE_NAMES_TO_FILES['m41.ttf'], 45)
        text_surface = font.render('Achtung!', True, TITLE_COLOR)
        rect = text_surface.get_rect(center=(SCREEN_WIDTH / 2, TITLE_MARGIN))
        self.screen_surface.blit(text_surface, rect)

    def drawScores(self):
        font = pygame.font.Font(FONT_FILE_NAMES_TO_FILES['menu_font.ttf'], 32)
        for i, player in enumerate(self.players):
            text = '%s: %d' % (player.color.name, player.score)
            text_surface = font.render(text, True, player.color.value)
            center_offset = SCREEN_WIDTH * (i + 1) / (len(self.players) + 1)
            rect = text_surface.get_rect(center=(center_offset, GUI_MARGIN - SCORES_MARGIN_BOTTOM))
            self.screen_surface.blit(text_surface, rect)

    def updateDisplay(self):
        self.screen_surface.blit(self.game_surface, (GAME_BORDER_WIDTH, GAME_BORDER_WIDTH + GUI_MARGIN))
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

    def playerCrashesIntoAnything(self, player):
        if self.playerCollidesWithWalls(player):
            return True

        for other_player in (p for p in self.players if p != player):
            if self.playerCollidesWithOtherPlayer(player, other_player):
                return True

        if self.playerCollidesWithItself(player):
            return True

        # Check other players' trails
        for trail in (p.trail for p in self.players if p != player):
            if self.playerCollidesWithTrail(player, trail):
                return True

    def playerCollidesWithWalls(self, player):
        x, y = player.position
        left_wall_collision = x - PLAYER_RADIUS < 0
        top_wall_collision = y - PLAYER_RADIUS < 0
        right_wall_collision = x + PLAYER_RADIUS > GAME_WIDTH
        bottom_wall_collision = y + PLAYER_RADIUS > GAME_HIGHT
        any_wall_collision = left_wall_collision or top_wall_collision or right_wall_collision or bottom_wall_collision
        return any_wall_collision

    def playerCollidesWithOtherPlayer(self, player, other_player):
        player_mask = pygame.mask.from_surface(player.surface)
        other_player_mask = pygame.mask.from_surface(other_player.surface)

        other_player_offset = Vec2d(other_player.surface_position) - Vec2d(player.surface_position)

        overlap_point = player_mask.overlap(other_player_mask, other_player_offset)
        if overlap_point is None:
            return False
        else:
            return True

    def playerCollidesWithItself(self, player):
        if USE_WEBCAM:
            return False
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

def main():
    global webcam
    if USE_WEBCAM:
        webcam = WebCam()
    game_screen = Screen()
    music_mixer = MusicMixer()
    game = Game(game_screen, music_mixer)
    game.start()
    exit_()

if "__main__" == __name__:
    main()
