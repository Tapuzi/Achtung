from pygame.locals import KEYDOWN, K_UP, K_DOWN, K_RETURN, K_ESCAPE, QUIT
import pygame
import menu
import sys


surface = pygame.display.set_mode((854,480)) #0,6671875 and 0,(6) of HD resoultion
surface.fill((51,51,51))
menu = menu.Menu()
menu.init(['Play (Set controls first)','Set Controls','Debug Options','Quit'], surface)
menu.draw()

pygame.key.set_repeat(199,69)#(delay,interval)
pygame.display.update()
while 1:
    for event in pygame.event.get():
        if event.type == KEYDOWN:
            if event.key == K_UP:
                menu.draw(-1) #here is the Menu class function
            if event.key == K_DOWN:
                menu.draw(1) #here is the Menu class function
            if event.key == K_RETURN:
                if menu.get_position() == 3:#here is the Menu class function
                    pygame.display.quit()
                    sys.exit()                        
            if event.key == K_ESCAPE:
                pygame.display.quit()
                sys.exit()
            pygame.display.update()
        elif event.type == QUIT:
            pygame.display.quit()
            sys.exit()
    pygame.time.wait(8)