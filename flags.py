
PLAYERS_COUNT = 1

USE_MOUSE = False
USE_WEBCAM = False
USE_ROBOTS = False

DEBUG = True
DEBUG_WEBCAM = False
DEUBG_WEBCAM_WITH_WINDOW = False
DEBUG_TRAIL = False
DEBUG_BONUSES = False
FULLSCREEN = False

DEBUG_WITHOUT_ROBOT = DEBUG and not USE_ROBOTS
DEBUG_SINGLE_PLAYER = DEBUG and PLAYERS_COUNT == 1

