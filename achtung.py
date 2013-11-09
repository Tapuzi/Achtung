"""
Achtung!
"""
from flags import *

import pygame
from collections import namedtuple
from vec2d import Vec2d
import random
import numpy
import os
from os import path

if DEBUG_WEBCAM:
    from WebCam import *
from Controllers import *

if DEBUG_WEBCAM:
    import cv2
    import cv2.cv as cv

##
## TODO:
##     - Fix the trail hole timing issues
##     - Add more sounds (player death, draw, win, ... maybe use DOTA/MortalKombat's announcer?)
##     - Add rounds and scores
##     - Change the _move function toke time-passed-since last tick into account,
##       so the players will always move the same distance, even if FPS drops.
##     - Support high speeds by drawing "circle lines" from the last point to the current point (?)
##       or try using http://pygamedraw.wordpress.com/ for trail drawing.
##     - Profile the game and improve performance (it seems that with multiple players / bigger window,
##       The drawing / collision detection slows the game down.
##       - Try to do things in parallel? (collision detection for example)
##       - Try to limit the mask overlap test are to that of the player's position (and radius)
##       - Maybe just use a lower target framerate
##     - Add a mode in between round that allows to drive robots back to the middle of the board?
##     - Add bonuses (speed up/down, control reverse, players swap, electrify etc...)
##     - Add black frame around board edges in size of game's width and height
##

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
    Color('Black', (0, 0, 0), (numpy.array([0, 0, 0],numpy.uint8),numpy.array([1, 1, 1],numpy.uint8))),
    Color('Red', (255, 0, 0), (numpy.array([160, 160, 60],numpy.uint8),numpy.array([180, 255, 255],numpy.uint8))),
    Color('Green', (0, 255, 0), (numpy.array([38, 140, 60],numpy.uint8), numpy.array([75, 255, 255],numpy.uint8))),
    Color('Blue', (0, 0, 255), (numpy.array([75, 80, 80],numpy.uint8), numpy.array([130, 255, 255],numpy.uint8))),
    Color('Yellow', (255, 255, 0), (numpy.array([20, 100, 100],numpy.uint8), numpy.array([38, 255, 255],numpy.uint8))),
]

IDS = ['1337' for color in COLORS]
COMPORTS = ['COM10']

ROBOT_RADIUS = 7
COLLISTION_RADIUS = ROBOT_RADIUS - 2

GAME_WIDTH = 500
GAME_HIGHT = 500

FPS_LIMIT = 60

OVERLAP_COLLISION_THRESHOLD = 10

TIME_TO_HOLE_MIN = 1.25 * 1000
TIME_TO_HOLE_MAX = 1.75 * 1000
HOLE_TIME_INTERVAL = 0.3 * 1000

NUMBER_OF_ROUNDS = 3

BACKGROUND_MUSIC_VOLUME_LOW = 0.3
BACKGROUND_MUSIC_VOLUME_NORMAL = 0.9

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

    def reset(self):
        self.last_point = None
        self.last_point_surface.fill((0, 0, 0, 0))
        self.surface.fill((0, 0, 0, 0))

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
        if self.last_point is not None:
            int_point = (int(point.x), int(point.y))
            last_point_int = (int(self.last_point.x), int(self.last_point.y))

            self.last_point_surface.fill((0, 0, 0, 0))
            pygame.draw.circle(self.last_point_surface, self.color.value, last_point_int, ROBOT_RADIUS)

            pygame.draw.circle(self.last_point_surface, (0, 0, 0, 0), int_point, ROBOT_RADIUS)
            self.surface.blit(self.last_point_surface, (0, 0))

    def draw(self):
        self.game_surface.blit(self.surface, (0, 0))


class Player:
    def __init__(self, game_surface, color, controller):
        self.game_surface = game_surface
        self.surface = pygame.Surface((GAME_WIDTH, GAME_HIGHT), flags=pygame.SRCALPHA)
        self.color = color
        self.lowerColor = color.value_range[0]
        self.upperColor = color.value_range[1]
        self.alive = True
        self.direction = None
        self.position = None
        self.trail = Trail(self.game_surface, color)
        self.controller = controller

        self._time_of_next_hole = None
        self._time_of_hole_end = None
        self._creating_hole = False
        self.resetTimers()

    def reset(self):
        self.alive = True
        self.trail.reset()

    def _set_position_and_direction_vector(self, position, direction_vector):
        self.position = position
        self.direction_vector = direction_vector

    def resetTimers(self):
        self.resetTimeOfNextHole()
        self.resetTimeOfHoleEnd()

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

        flags = 0
        if FULLSCREEN:
            flags |= pygame.FULLSCREEN
        self.screen = pygame.display.set_mode((GAME_WIDTH, GAME_HIGHT), flags)
        if FULLSCREEN:
            # It takes some time for the screen to adjust,
            # so wait to let the game begin when the screen is ready.
            pygame.time.wait(2000)

        self.surface = pygame.Surface(self.screen.get_size())
        self.clock = pygame.time.Clock()

        self.music_file = random.choice(MUSIC_FILES)
        pygame.mixer.music.load(self.music_file)

        self.begin_sound = pygame.mixer.Sound(SOUND_FILE_NAMES_TO_FILES['begin.wav'])
        self.start_beeps_sound = pygame.mixer.Sound(SOUND_FILE_NAMES_TO_FILES['start_beeps.wav'])
        self.explosion_sound = pygame.mixer.Sound(SOUND_FILE_NAMES_TO_FILES['80938__tony-b-kksm__soft-explosion.wav'])

        if DEBUG_KEYBOARD:
            self.controllers = [KeyboardController(pygame.K_LEFT, pygame.K_RIGHT)]
            if DEBUG_KEYBOARD_TWO_PLAYERS:
                self.controllers.append(KeyboardController(pygame.K_z, pygame.K_c))
        elif DEBUG_MOUSE:
            self.controllers = [MouseController()]
        else:
            self.controllers = [WatchController(port, id) for port, id in zip(COMPORTS, IDS)]

        self.players = [Player(self.surface, color, controller) for color, controller in zip(COLORS, self.controllers)]
        self.players_alive = self.players[:]
        self.end_state = None
        self.round_number = None

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

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pygame.quit()

    def kill_player(self, player):
        player.die()
        self.explosion_sound.play()
        self.players_alive.remove(player)

    def handle_events(self):
        events = []
        for event in pygame.event.get():
            events.append(event)
            if event.type == pygame.QUIT:
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    exit()
        return events

    def start(self):
        self.mode = 'pre_round_wait'

        pygame.mixer.music.set_volume(BACKGROUND_MUSIC_VOLUME_LOW)
        pygame.mixer.music.play(loops=-1)

        for round_number in range(1, NUMBER_OF_ROUNDS + 1):
            self.round_number = round_number
            self.play_round()

        print 'Game over'

    def play_round(self):
        for player in self.players:
            player.reset()
        self.players_alive = self.players[:]

        if DEBUG:
            self._randomize_players_positions_and_direction_vectors()

        self.pre_round_wait()
        self.pre_round_start()
        self.do_play_round()
        self.round_end()



    def pre_round_wait(self):
        while True:
            self.handle_events()

            self.clearSurface()
            for player in self.players:
                player.updatePosition()
                player.draw()
            self.updateDisplay()

            pressed_keys = pygame.key.get_pressed()
            if pressed_keys[pygame.K_SPACE] or pressed_keys[pygame.K_RETURN]:
                break

            self.tick()

    def pre_round_start(self):
        sound_length = self.start_beeps_sound.get_length()
        current_time = pygame.time.get_ticks()
        sound_end_time = current_time + int(sound_length * 1000)
        self.start_beeps_sound.play()
        while True:
            self.handle_events()
            # TODO: display on the Screen 3, 2, 1, Begin!
            if pygame.time.get_ticks() >= sound_end_time:
                break
            self.tick()

        pygame.mixer.music.set_volume(BACKGROUND_MUSIC_VOLUME_NORMAL)

        self.begin_sound.play()
        for player in self.players:
            player.resetTimers()

    def do_play_round(self):
        paused = False

        while True:
            events = self.handle_events()
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        paused = not paused

            if not paused:
                for player in self.players_alive[:]:
                    try:
                        player.updatePosition()
                        player.updateDirection()
                    except RobotNotFoundError:
                        self.kill_player(player)

                self.clearSurface()
                for player in self.players:
                    player.trail.draw()
                    player.draw()
                self.updateDisplay()

                for player in self.players_alive[:]:
                    if self.playerColidesWithWalls(player):
                        self.kill_player(player)

                    for trail in (player.trail for player in self.players):
                        if self.playerColidesWithTrail(player, trail):
                            self.kill_player(player)

                # Check end conditions
                if len(self.players_alive) == 0:
                    self.end_state = 'draw'
                    break
                elif len(self.players_alive) == 1:
                    self.end_state = 'win'
                    winner = self.players_alive[0]
                    if not DEBUG_SINGLE_PLAYER:
                        break

                if DEBUG:
                    for player in self.players_alive:
                        player._move()

            self.tick()

    def round_end(self):
        if self.end_state == 'draw':
            message = 'Draw.'
        elif self.end_state == 'win':
            message = '%s is he Winner!' % winner.color.name
        else:
            message = 'WTF?'

        print message

        pygame.mixer.music.set_volume(BACKGROUND_MUSIC_VOLUME_LOW)

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
    global webcam
    with Game() as game:
        if DEBUG_WEBCAM:
            webcam = WebCam()
        game.start()

if "__main__" == __name__:
    main()
