from Controllers import *
import time
import pygame

pygame.init()
c = XboxController()
while True:
        d = c.getDirection()
        if d == STRAIGHT:
            print "Straight"
        elif d== LEFT:
            print "Left"
        elif d == RIGHT:
            print "Right"
        else:
            print "NOTHING"
        #time.sleep(1)
