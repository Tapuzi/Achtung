import cv2

def checkWebcam(camNum):
	capt = cv2.VideoCapture(0)
	while True:
		ret, frame = capt.read()
		if ret:
			cv2.imshow('webcam', frame)
			k = cv2.waitKey(1)
			if k == 27:
				break
	cv2.destroyAllWindows()
	
	
def main():
  checkWebcam(0)
  
  
if __name__ == "__main__":
  main()
