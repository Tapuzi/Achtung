import cv2
import numpy as np
import time

DEBUG_PRINT = True

class webCam(object):
    def __init__(self, camNum):
        self.capture = cv2.VideoCapture(camNum)
        self.lowerH = 0
        self.lowerS = 0
        self.lowerV = 0

        self.upperH = 180
        self.upperS = 256
        self.upperV = 256
        
    def getPositions(self, *args):
        self.lowerH = cv2.getTrackbarPos('lowerH', "triangle")
        self.lowerS = cv2.getTrackbarPos('lowerS', "triangle")
        self.lowerV = cv2.getTrackbarPos('lowerV', "triangle")

        self.upperH = cv2.getTrackbarPos('upperH', "triangle")
        self.upperS = cv2.getTrackbarPos('upperS', "triangle")
        self.upperV = cv2.getTrackbarPos('upperV', "triangle")
        
    def threshholdFrame(self, frame):
        return cv2.inRange(frame, np.array([self.lowerH, self.lowerS, self.lowerV],np.uint8), np.array([self.upperH, self.upperS, self.upperV],np.uint8))

    def initializeWindows(self):
        cv2.namedWindow("triangle")
        cv2.namedWindow("video")
        
        cv2.createTrackbar('lowerH', "triangle", 0, 180, self.getPositions)
        cv2.createTrackbar('upperH', "triangle", 180, 180, self.getPositions)
        
        cv2.createTrackbar('lowerS', "triangle", 0, 255, self.getPositions)
        cv2.createTrackbar('upperS', "triangle", 256, 255, self.getPositions)
        
        cv2.createTrackbar('lowerV', "triangle", 0, 255, self.getPositions)
        cv2.createTrackbar('upperV', "triangle", 256, 255, self.getPositions)

    
def main():
    if DEBUG_PRINT:
        lastColors = ()
    time.sleep(5)
    webcam = webCam(2)
    webcam.initializeWindows()
    while True:
        ret, frame = webcam.capture.read()
        if ret:
            webcam.getPositions()
            hsvFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            threshedFrame = webcam.threshholdFrame(hsvFrame)
            cv2.imshow("triangle", threshedFrame)
            cv2.imshow("video", frame)
            if DEBUG_PRINT:
                newColors = (webcam.lowerH, webcam.lowerS, webcam.lowerV, webcam.upperH, webcam.upperS, webcam.upperV)
                if newColors != lastColors:
                    print "numpy.array([%d, %d, %d],numpy.uint8), numpy.array([%d, %d, %d], numpy.uint8)" % newColors
                    lastColors = newColors
            key = cv2.waitKey(80)
            if key == 27:
                break
                
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
