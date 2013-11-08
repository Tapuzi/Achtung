import cv2, achtung
imPath=r"C:\Users\Dor\Documents\GitHub\Achtung\Images\Images For Testing\Board1.jpg"

origIm = cv2.imread(imPath)
def testWarp(orig, thresh):
    im = achtung.WebCam.fixCap(orig, thresh)
    cv2.imshow('im', im)
    cv2.waitKey(1)

import achtung
testWarp(origIm, 135)