import pygame
import time

pygame.init()
controller = pygame.joystick.Joystick(0)
controller.init()

while True:
    left_axis = [controller.get_axis(0), controller.get_axis(1)]
    right_axis = [controller.get_axis(2), controller.get_axis(3)]
    print left_axis, right_axis
    time.sleep(1)
