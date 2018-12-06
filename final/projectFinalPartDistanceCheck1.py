import cv2
import numpy as np
from picamera.array import PiRGBArray
import picamera
import time
import io
import math
import RPi.GPIO as GPIO
from RpiMotorLib import RpiMotorLib


#define GPIO pins
#GPIO.cleanup()
GPIO_pinsY = (14, 15, 18) # Microstep Resolution MS1-MS3 -> GPIO Pin
directionY = 16       # Direction -> GPIO Pin
stepY = 21      # Step -> GPIO Pin

GPIO_pinsX = (5, 6, 13) # Microstep Resolution MS1-MS3 -> GPIO Pin
directionX = 23       # Direction -> GPIO Pin
stepX = 24      # Step -> GPIO Pin

# Declare an named instance of class pass GPIO pins numbers
mymotortestY = RpiMotorLib.A4988Nema(directionY, stepY, GPIO_pinsY, "A4988")
mymotortestX = RpiMotorLib.A4988Nema(directionX, stepX, GPIO_pinsX, "A4988")

# call the function, pass the arguments


xPoint = []
yPoint = []
count = 0
xOld = 1000
yOld = 1000
isStartTracking = False
xPoints = []
yPoints = []
xmin = 0
xmax = 700
ymin = 0
ymax = 700
firstTime = False
blobDetection = False

with picamera.PiCamera() as camera:

    try:
        camera.resolution = (320, 320)
        camera.framerate = 32
        
        rawCapture = PiRGBArray(camera, size=(320, 320))

        time.sleep(2)
        detector = cv2.SimpleBlobDetector_create()

        #Create old frame
        for frames in camera.capture_continuous(rawCapture, format="rgb", use_video_port=True):
            frame = frames.array
            #frame = cv2.flip(frame,0)
            #frame = cv2.flip(frame,1)
            old_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            
            rawCapture.truncate()
            rawCapture.seek(0)
            break

        # Lucas Kanade params
        lk_params = dict(winSize = (15, 15), maxLevel = 4,
                         criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

        # Mouse function
        
        def select_point(event, x, y, flags, params):
            global point, point_selected, old_points, count, xPoint, yPoint,isStartTracking, xOld, yOld,xInitial,yInitial
            
            if event == cv2.EVENT_LBUTTONDOWN:
                point = (x, y)
                xInitial = x
                yInitial = y
                point_selected = True
                old_points = np.array([[x, y]], dtype=np.float32)

        cv2.namedWindow("Frame")
        cv2.setMouseCallback("Frame", select_point)
        point_selected = False
        flag = True
        point = ()
        old_points = np.array([[]])
        for frames in camera.capture_continuous(rawCapture, format="rgb", use_video_port=True):
            frame = frames.array
            #frame = np.asarray(frames)
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if blobDetection == False:
                keypoints = detector.detect(gray_frame)
                for keypoint in keypoints:
                    x = int(keypoint.pt[0])
                    y = int(keypoint.pt[1])
                    cv2.circle(frame, (x, y), 5, (0,255,0), -1)
                    #print("X:",x,"Y:",y)
                    if firstTime == False:
                        xmin = x
                        xmax = x
                        ymin = y
                        ymax = y
                        firstTime = True
                    if(firstTime == True):
                        if(x < xmin):
                            xmin = x
                        if(x > xmax):
                            xmax = x
                        if(y < ymin):
                            ymin = y
                        if(y > ymax):
                            ymax = y
                    cv2.circle(frame, (x, y), 5, (0,255,0), -1)
                    blobDetection = True
                    count = 5

            if point_selected is True:
               #GPIO.cleanup()
               #GPIO_pinsY = (14,15,18)
                directionY = 20
                stepY = 21
               #GPIO_pinsX = (5,6,13)
                directionX = 23
                stepX = 24
                xOld, yOld = old_points.ravel()
                cv2.circle(frame, point, 5, (0,0,255), 2)
                new_points, status, error = cv2.calcOpticalFlowPyrLK(old_gray, gray_frame, old_points, None, **lk_params)
                old_gray = gray_frame.copy()
                old_points = new_points
                x, y = new_points.ravel()

                if(count >= 4):
                    xRange = abs(xmax-xmin)           #abs(xPoint[0] - xPoint[1])
                    yRange = abs(ymax-ymin)                        #abs(yPoint[0] - yPoint[2])
                    print("Xrange:",xRange, "Xblob:", abs(xmin-xmax))
                    xcm = (abs(x-xInitial)*10)/xRange
                    ycm = (abs(y-yInitial)*10)/yRange
                   # print("Distance...X: ", xcm, "Y: ",ycm)
                    if((y >= (yOld-5)) and (y <= (yOld+5))):
                        steps = int(round(56 * ycm))
                        if (y > yOld):
                            print("\nY Steps:",steps)
                            mymotortestY.motor_go(1, "Full" , steps, .0005, False, .05)
                        else:
                            print("\n-Y Steps:",steps)
                            mymotortestY.motor_go(0, "Full" , steps, .0005, False, .05)
                        yInitial = y
                       # print("Steps : ", steps)
                    if((x >= (xOld-5)) and (x <= (xOld+5))):
                        steps = int(round(56 * xcm))
                        if (x > xOld):
                            print("\nX Steps:",steps)
                            mymotortestX.motor_go(0, "Full" , steps, .0005, False, .05)
                        else:
                            print("\n-X Steps:",steps)
                            mymotortestX.motor_go(1, "Full" , steps, .0005, False, .05)
                        xInitial = x
                       # print("StepsX ", steps)
                    #flag = True
                    #if flag is True:
                     #   mymotortestX.motor_go(True, "Full" , 100, .0005, False, .05)
                     #   flag = False
                cv2.circle(frame, (x, y), 5, (0,255,0), -1)
                
                

            cv2.imshow("Frame", frame)
            

            key = cv2.waitKey(1)
            
            rawCapture.truncate()
            rawCapture.seek(0)
            if key == ord("q"):
                break

        #camera.release()
        cv2.destroyAllWindows()

    finally:
        #camera.stop_preview()
#        GPIO.cleanup()
        print("Stopped")
