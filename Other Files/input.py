import pygame, os

pygame.init()

class Input:
	def __init__(self):
		pygame.init()
		
	def DebugPrintPressedLetters(self):
		# Setup
		myFont = pygame.font.Font(r"C:\Windows\Fonts\ahronbd.ttf", 35)
		color = (255,0,0)
		screen = pygame.display.set_mode([400,100])
		pygame.display.set_caption("Press Esc to quit (return to console)")
		keysRepresentation = {pygame.K_BACKQUOTE: '\\', pygame.K_a: 'a', pygame.K_b: 'b', pygame.K_c: 'c', pygame.K_d: 'd', pygame.K_e: 'e', pygame.K_f: 'f', pygame.K_g: 'g', pygame.K_h: 'h', pygame.K_i: 'i', pygame.K_j: 'j', pygame.K_k: 'k', pygame.K_l: 'l', pygame.K_m: 'm', pygame.K_n: 'n', pygame.K_o: 'o', pygame.K_p: 'p', pygame.K_q: 'q', pygame.K_r: 'r', pygame.K_s: 's', pygame.K_t: 't', pygame.K_u: 'u', pygame.K_v: 'v', pygame.K_w: 'w', pygame.K_x: 'x', pygame.K_y: 'y', pygame.K_z: 'z'}
		mainloop = True
		pressedKeys = []
		while mainloop:
			# Empty screen
			screen.fill((255,255,255))
			# Set an array of pressed keys, and handle ESC for quit
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					mainloop = False
				elif event.type == pygame.KEYDOWN:
					pressedKeys.append(event.key)
					if event.key == pygame.K_ESCAPE:
						mainloop = False
				elif event.type == pygame.KEYUP:
					if event.key in pressedKeys:
						pressedKeys.remove(event.key)
			
			# Represent!
			outStringChars = ( keysRepresentation[key] for key in pressedKeys if key in keysRepresentation.keys() )
			screen.blit(myFont.render("Pressed keys: " + ''.join(outStringChars), 1, (color)), (0,0))
			pygame.display.update()
		
		# End of the loop
		pygame.display.quit()
		
def DebugInput():
	inputEngine = Input()
	inputEngine.DebugPrintPressedLetters()