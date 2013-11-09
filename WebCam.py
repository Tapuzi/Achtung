'''This file includes webcam functions'''

import cv2

class WebCam:
    def __init__(self):
        self.webCamCapture = cv2.VideoCapture(0)
        self.webCamCapture.set(cv.CV_CAP_PROP_FRAME_WIDTH, GAME_WIDTH)
        self.webCamCapture.set(cv.CV_CAP_PROP_FRAME_HEIGHT, GAME_HIGHT)
        self.webCamCapture.set(cv2.cv.CV_CAP_PROP_FPS, FPS_LIMIT)
    
    
    def testRectify(self, thSense):
        while True:
            ret, frame = self.webCamCapture.read()
            if ret:
                frame = self.fixCap(frame, thSense)
                cv2.imshow('webcam', frame)
                k = cv2.waitKey(1)
                if k == 27:
                    break
        cv2.destroyAllWindows()
    
    def testContours(self):
        while True:
            ret, frame = self.webCamCapture.read()
            if ret:
                frame = self.showContours(frame)
                cv2.imshow('webcam', frame)
                k = cv2.waitKey(1)
                if k == 27:
                    break
        cv2.destroyAllWindows()
    
    @staticmethod
    def rectify(h):
        ''' this function put vertices of square of the board, in clockwise order '''
        h = h.reshape((4,2))
        hnew = numpy.zeros((4,2),dtype = numpy.float32)
        
        add = h.sum(1)
        hnew[0] = h[numpy.argmin(add)]
        hnew[2] = h[numpy.argmax(add)]
        
        diff = numpy.diff(h,axis = 1)
        hnew[1] = h[numpy.argmin(diff)]
        hnew[3] = h[numpy.argmax(diff)]
    
        return hnew
    
    @staticmethod
    def showContours(frame):
        '''Spots contours and returns a frame with the spotted contours'''
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255,1,1,5,2)
        contours = None
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours == None:
            return frame
        image_area = gray.size
        
        print len(contours)
        for i in contours:
            if cv2.contourArea(i) > image_area/2:
                cv2.drawContours(frame,contours,1,(0,255,0),3)
        
        return frame
        
    @staticmethod
def fixCap(frame):
    maxContourArea = 0
    maxCnt = 0
    maxApprox = 0

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255,1,1,11,2)
    contours, hier = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
	    for cnt in contours:
		cntArea = cv2.contourArea(cnt)
		peri = cv2.arcLength(cnt,True)
		approx = cv2.approxPolyDP(cnt, 0.02*peri, True)
		if len(approx) == 4 and cntArea > maxContourArea:
		    maxContourArea = cntArea
		    maxCnt = cnt
		    maxApprox = approx

    if maxContourArea > 0:
        newSize = numpy.array([ [0,0],[GAME_WIDTH,0],[GAME_WIDTH, GAME_HIGHT],[0,GAME_HIGHT] ],numpy.float32)
        reOrderApprox = WebCam.rectify(maxApprox)
        retval = cv2.getPerspectiveTransform(reOrderApprox,newSize)
        warp = cv2.warpPerspective(frame,retval,(GAME_WIDTH, GAME_HIGHT))
        return warp
    
    return frame