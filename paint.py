""" paint.py
    a simple paint program"""

import pygame

def checkKeys(myData):
    """test for various keyboard inputs"""

    #extract the data
    (event, background, drawColor, lineWidth, keepGoing) = myData
    #print myData

    if event.key == pygame.K_q:
        #quit
        keepGoing = False
    elif event.key == pygame.K_c:
        #clear screen
        background.fill((255, 255, 255))
    elif event.key == pygame.K_s:
        #save picture
        pygame.image.save(background, "painting.bmp")
    elif event.key == pygame.K_l:
        #load picture
        background = pygame.image.load("painting.bmp")
    elif event.key == pygame.K_r:
        #red
        drawColor = (255, 0, 0)
    elif event.key == pygame.K_g:
        #green
        drawColor = (0, 255, 0)
    elif event.key == pygame.K_w:
        #white
        drawColor = (255, 255, 255)
    elif event.key == pygame.K_b:
        #blue
        drawColor = (0, 0, 255)
    elif event.key == pygame.K_k:
        #black
        drawColor = (0, 0, 0)

    #line widths
    elif event.key == pygame.K_1:
        lineWidth = 1
    elif event.key == pygame.K_2:
        lineWidth = 2
    elif event.key == pygame.K_3:
        lineWidth = 3
    elif event.key == pygame.K_4:
        lineWidth = 4
    elif event.key == pygame.K_5:
        lineWidth = 5
    elif event.key == pygame.K_6:
        lineWidth = 6
    elif event.key == pygame.K_7:
        lineWidth = 7
    elif event.key == pygame.K_8:
        lineWidth = 8
    elif event.key == pygame.K_9:
        lineWidth = 9

    #return all values
    myData = (event, background, drawColor, lineWidth, keepGoing)
    return myData

def showStats(drawColor, lineWidth):
    """ shows the current statistics """
    myFont = pygame.font.SysFont("None", 20)
    stats = "color: %s, width: %d" % (drawColor, lineWidth)
    statSurf = myFont.render(stats, 1, (drawColor))
    return statSurf

def main():
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    pygame.display.set_caption("Paint:  (r)ed, (g)reen, (b)lue, (w)hite, blac(k), (1-9) width, (c)lear, (s)ave, (l)oad, (q)uit")

    background = pygame.Surface(screen.get_size())
    background.fill((255, 255, 255))

    clock = pygame.time.Clock()
    keepGoing = True
    lineStart = (0, 0)
    drawColor = (0, 0, 0)
    lineWidth = 3

    prev = None
    while keepGoing:
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                keepGoing = False
##            elif event.type == pygame.MOUSEBUTTONDOWN:
##                point = pygame.mouse.get_pos()
##                if prev:
##                    background.fill((255, 255, 255))
##                    drawSmoothLine(background, drawColor, prev, point, 5)
##                    prev = None
##                else:
##                    prev = point
            elif event.type == pygame.MOUSEMOTION:
                lineEnd = pygame.mouse.get_pos()
                if pygame.mouse.get_pressed() == (1, 0, 0):
                    drawSmoothLine(background, drawColor, lineStart, lineEnd, lineWidth)
                lineStart = lineEnd
            elif event.type == pygame.KEYDOWN:
                myData = (event, background, drawColor, lineWidth, keepGoing)
                myData = checkKeys(myData)
                (event, background, drawColor, lineWidth, keepGoing) = myData
        screen.blit(background, (0, 0))
        myLabel = showStats(drawColor, lineWidth)
        screen.blit(myLabel, (450, 450))
        pygame.display.flip()

    pygame.quit()

def drawSmoothLine(surface, color, start, end, width):
    pygame.draw.line(surface, color, start, end, width)

    start_x, start_y = start
    end_x, end_y = end

    #pygame.draw.line(surface, color, (start_x + 50, start_y), (end_x + 50, end_y), width)

    delta_x = end_x - start_x
    delta_y = end_y - start_y

    if delta_x == 0 or delta_y == 0:
        return

    slope = abs(float(delta_y) / delta_x)

    half_width = width / 2.0
    if slope < 1:
        pygame.draw.aaline(surface, color, (start_x, start_y - half_width), (end_x, end_y - half_width))
        pygame.draw.aaline(surface, color, (start_x, start_y + half_width), (end_x, end_y + half_width))
    else:
        pygame.draw.aaline(surface, color, (start_x - half_width, start_y), (end_x - half_width, end_y))
        pygame.draw.aaline(surface, color, (start_x + half_width, start_y), (end_x + half_width, end_y))


if __name__ == "__main__":
    main()