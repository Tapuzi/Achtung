import cv2
import cv2.cv as cv
import numpy as np

"""
image detection function to detect the robots on board,
integrates with main.py
things to add:
* multithreading?
* detecting direction of robot
* structre it in class
* more......
"""

def detectBot(webCamFrame, robots):
	""" locates all playing robots and sets their new location """
    img = cv2.GaussianBlur(webCamFrame, (5,5), 0)
    img = cv2.cvtColor(webCamFrame, cv2.COLOR_BGR2HSV) # changes from RGB to HSV
    
	for bot in robots:
        binaryColor = cv2.inRange(img, bot.color.upper, bot.color.lower) # #creating a threshold image that contains pixels in between color Upper and Lower
        dilation = np.ones((15, 15), "uint8") 
        binaryColor = cv2.dilate(binaryColor, dilation) # cnverts array to binaryArray
        contours, hier = cv2.findContours(binaryColor, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE) # find all shapes of color
        for cnt in contours: # for each shape
            moments = cv2.moments(cnt) # get shapes properties
            area = moments['m00'] # get shape area
            if area > 1000: # because it's a webCam picture with many noises, we only check shapes with area larger then 1000, we need to adjust this value to get perfect results
                approx = cv2.approxPolyDP(cnt,0.05*cv2.arcLength(cnt,True),True) # get shape Sides
                if len(approx) == 3: # if 3 sides thenh - TRIANGLE!!
                    bot.location.x = moments['m10'] / area # get x position of the center of the triangle
                    bot.location.y = moments['m01'] / area # get x position of the center of the triangle
					
def main():
    webCamCapture = cv2.VideoCapture(0) # get webCam stream / can change the 0 to filename
    while True: 
        ret, frame = webCamCapture.read() # ret value true if capture from webCam went good, frame is the picture from the webCam
        if ret == True:
            detectBots(frame, playingRobots) #frame is frame, playingRobots is the array of all robots that are still playing
			
if __name__ == "__main__":
	main()
