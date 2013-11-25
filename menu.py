'''
@author: avalanchy (at) google mail dot com
@version: 0.1; python 2.7; pygame 1.9.2pre; SDL 1.2.14; MS Windows XP SP3
@date: 2012-04-08
@license: This document is under GNU GPL v3

README on the bottom of document.

@font: from http://www.dafont.com/coders-crux.font
      more abuot license you can find in data/coders-crux/license.txt
'''

import pygame
from pygame.locals import *

if not pygame.display.get_init():
    pygame.display.init()

if not pygame.font.get_init():
    pygame.font.init()

MENU_BACKGROUND_COLOR = (51, 51, 51)

class Menu:
    list = []
    pola = []
    size_font = 32
    font_path = r'Fonts\menu_font.ttf'
    font = pygame.font.Font
    dest_surface = pygame.Surface
    number_pol = 0
    color_tla = (51,51,51)
    color_text =  (255, 255, 153)
    color_selection = (153,102,255)
    position_selection = 0
    position_embed = (0,0)
    menu_width = 0
    menu_height = 0

    class Pole:
        tekst = ''
        pole = pygame.Surface
        pole_rect = pygame.Rect
        selection_rect = pygame.Rect

    def move_menu(self, top, left):
        self.position_embed = (top,left) 

    def set_colors(self, text, selection, background):
        self.color_tla = background
        self.color_text =  text
        self.color_selection = selection
        
    def set_fontsize(self,font_size):
        self.size_font = font_size
        
    def set_font(self, path):
        self.font_path = path
        
    def get_position(self):
        return self.position_selection
    
    def init(self, list, dest_surface):
        self.list = list
        self.dest_surface = dest_surface
        self.number_pol = len(self.list)
        self.create_structure()        
        
    def draw(self,move=0):
        if move:
            self.position_selection += move 
            if self.position_selection == -1:
                self.position_selection = self.number_pol - 1
            self.position_selection %= self.number_pol
        menu = pygame.Surface((self.menu_width, self.menu_height))
        menu.fill(self.color_tla)
        selection_rect = self.pola[self.position_selection].selection_rect
        pygame.draw.rect(menu,self.color_selection,selection_rect)

        for i in xrange(self.number_pol):
            menu.blit(self.pola[i].pole,self.pola[i].pole_rect)
        self.dest_surface.blit(menu,self.position_embed)
        return self.position_selection

    def create_structure(self):
        moveiecie = 0
        self.menu_height = 0
        self.font = pygame.font.Font(self.font_path, self.size_font)
        for i in xrange(self.number_pol):
            self.pola.append(self.Pole())
            self.pola[i].tekst = self.list[i]
            self.pola[i].pole = self.font.render(self.pola[i].tekst, 1, self.color_text)

            self.pola[i].pole_rect = self.pola[i].pole.get_rect()
            moveiecie = int(self.size_font * 0.2)

            height = self.pola[i].pole_rect.height
            self.pola[i].pole_rect.left = moveiecie
            self.pola[i].pole_rect.top = moveiecie+(moveiecie*2+height)*i

            width = self.pola[i].pole_rect.width+moveiecie*2
            height = self.pola[i].pole_rect.height+moveiecie*2            
            left = self.pola[i].pole_rect.left-moveiecie
            top = self.pola[i].pole_rect.top-moveiecie

            self.pola[i].selection_rect = (left,top ,width, height)
            if width > self.menu_width:
                    self.menu_width = width
            self.menu_height += height
        x = self.dest_surface.get_rect().centerx - self.menu_width / 2
        y = self.dest_surface.get_rect().centery - self.menu_height / 2
        mx, my = self.position_embed
        self.position_embed = (x+mx, y+my) 


if __name__ == "__main__":
    import sys
    surface = pygame.display.set_mode((854,480)) #0,6671875 and 0,(6) of HD resoultion
    surface.fill((51,51,51))
    '''First you have to make an object of a *Menu class.
    *init take 2 arguments. List of fields and destination surface.
    Then you have a 4 configuration options:
    *set_colors will set colors of menu (text, selection, background)
    *set_fontsize will set size of font.
    *set_font take a path to font you choose.
    *move_menu is quite interseting. It is only option which you can use before 
    and after *init statement. When you use it before you will move menu from 
    center of your surface. When you use it after it will set constant coordinates. 
    Uncomment every one and check what is result!
    *draw will blit menu on the surface. Be carefull better set only -1 and 1 
    arguments to move selection or nothing. This function will return actual 
    position of selection.
    *get_postion will return actual position of seletion. '''
    menu = Menu()#necessary
    #menu.set_colors((255,255,255), (0,0,255), (0,0,0))#optional
    #menu.set_fontsize(64)#optional
    #menu.set_font('data/couree.fon')#optional
    #menu.move_menu(100, 99)#optional
    menu.init(['Start','Options','Quit'], surface)#necessary
    #menu.move_menu(0, 0)#optional
    menu.draw()#necessary
    
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
                    if menu.get_position() == 2:#here is the Menu class function
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
        
        
class MenuWrapper():
    def __init__(self, screen, clock, music_mixer, music_file = r'music\Menu music\MenuMusic - Threshold 8 bit.ogg', fps_limit = None):
        self.screen = screen
        self.clock = clock
        self.music_mixer = music_mixer
        self.music_file = music_file
        self.fps_limit = fps_limit
        self.current_selection = 0
        
        self.options = []
        self.functions = []
        self.exit_function = None

    def _addOption(self, caption, function = None):
        self.options.append(caption)
        self.functions.append(function)
            
    def setOptions(self, options):
        self.options = []
        self.functions = []
        for caption, function in options:
            self._addOption(caption, function)
            
    def setExitFunction(self, function):
        self.exit_function = function
        
    def showMenu(self):
        if [] == self.options: # If there are no menu items, return self.exit_function
            return self.exit_function

        # Start menu music!
        if None != self.music_file:
            self.music_mixer.setBackgroundMusic(self.music_file)

        self.screen.fill(MENU_BACKGROUND_COLOR)

        current_menu = Menu()
        current_menu.init(self.options, self.screen)
        current_menu.draw()
        self.current_selection = current_menu.get_position()

        pygame.display.update()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.locals.KEYDOWN:
                    if event.key == pygame.locals.K_UP:
                        current_menu.draw(-1)
                    elif event.key == pygame.locals.K_DOWN:
                        current_menu.draw(1)
                    elif event.key in [pygame.locals.K_RETURN, pygame.K_KP_ENTER]:
                        self.current_selection = current_menu.get_position()
                        if None != self.functions[self.current_selection]:
                            return self.functions[self.current_selection]
                    elif event.key == pygame.locals.K_ESCAPE:
                        return self.exit_function
                    pygame.display.update()
                elif event.type == pygame.locals.QUIT:
                    return self.exit_function
                    
            if None != self.fps_limit:
                self.clock.tick(FPS_LIMIT)
                current_fps = self.clock.get_fps()
                pygame.display.set_caption("FPS: %f" % current_fps)