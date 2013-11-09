

# Uncomment your's when you are working
DEBUGGER = 'hjbyt'
##DEBUGGER = 'X-reX'
##DEBUGGER = 'Shleime'
##DEBUGGER = 'papaya91'
##DEBUGGER = 'alon7'

#
# Defaults
#

DEBUG = True
DEBUG_WEBCAM = True
DEUBG_WEBCAM_WITH_WINDOW = False
DEBUG_KEYBOARD = False
DEBUG_KEYBOARD_TWO_PLAYERS = False
DEBUG_MOUSE = False
DEBUG_TRAIL = False
FULLSCREEN = True


#
# Debugger specific
#

try:
    if DEBUGGER == 'hjbyt':
        DEBUG = True
        DEBUG_WEBCAM = False
        DEUBG_WEBCAM_WITH_WINDOW = False
        DEBUG_KEYBOARD = True
        DEBUG_KEYBOARD_TWO_PLAYERS = False
        DEBUG_MOUSE = False
        DEBUG_TRAIL = False
        FULLSCREEN = False
    elif DEBUGGER == 'X-reX':
        pass
    elif DEBUGGER == 'Shleime':
        pass
    elif DEBUGGER == 'papaya91':
        pass
    elif DEBUGGER == 'alon7':
        pass
except NameError:
    # DEBUGGER not defined
    pass

#
# Derivatives
#

DEBUG_SINGLE_PLAYER = DEBUG and not DEBUG_KEYBOARD_TWO_PLAYERS