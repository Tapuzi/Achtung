import cv2

def checkWebcam(camNum):
    capt = cv2.VideoCapture(0)
    while True:
        ret, frame = capt.read()
        if ret:
            newFrame = findBorder(frame)
            cv2.imshow('webcam', newFrame)
            k = cv2.waitKey(1)
            if k == 27:
                break
    cv2.destroyAllWindows()



def findBorder(frame):
        """find game's borders"""
        maxContourArea = 0
         #minimum borders size
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

        cv2.drawContours(frame,[maxCnt],-1,(0,255,0),3)
        print maxContourArea
        return frame

def main():
  checkWebcam(0)


if __name__ == "__main__":
  main()
