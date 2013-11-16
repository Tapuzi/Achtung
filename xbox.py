import pygame
import time
import math
 
# init controller
pygame.init()
controller = pygame.joystick.Joystick(0)
controller.init()
print 'Xbox Controller Connected'

print '/**************************/'
print 'Joystick Drive Program'
print "Press 'q' to quit"
print '/**************************/'
 
key = 0
y = 0
x = 0
while key != 'q':
    for event in pygame.event.get():
        if event.type == pygame.JOYAXISMOTION:
            if event.axis == 4:
                x = event.value
                if math.fabs(x) < 0.95:
                    x = 0

    # send to arduino
    command = ' '
    if x < 0:
        command = 'a'
    elif x > 0:
        command = 'd'
    if command != ' ':
        print command

    time.sleep(0.5)
