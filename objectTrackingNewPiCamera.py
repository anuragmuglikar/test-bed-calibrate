import cv2
import numpy as np
from picamera.array import PiRGBArray
#from picamera import PiCamera
import picamera
import time
import io
from RPLCD.i2c import CharLCD
import math

lcd = CharLCD('MCP23008', 0x24)
#lcd.write_string('Hello')
uparrow = (
0b00100,
0b01110,
0b11111,
0b11111,
0b00100,
0b00100,
0b00100,
0b00100)

downarrow = (
0b00100,
0b00100,
0b00100,
0b00100,
0b11111,
0b11111,
0b01110,
0b00100)

lcd.create_char(0,uparrow)
lcd.create_char(1,downarrow)
lcd.cursor_pos = (1,8)
lcd.write(0)
lcd.cursor_pos = (0,8)
lcd.write(1)
lcd2 = CharLCD('MCP23008', 0x20)


lcd2.create_char(0,uparrow)
lcd2.create_char(1,downarrow)
lcd2.cursor_pos = (1,8)
lcd2.write(0)
lcd2.cursor_pos = (0,8)
lcd2.write(1)
time.sleep(20)
#lcd2.write_string('world')
#lcd.clear()
#lcd2.clear()

lcd.cursor_mode = "blink"
lcd2.cursor_mode = "blink"
#xPoint1 = 236
#yPoint1 = 386

#xPoint2 = 606
#yPoint2 = 398

#xPoint3 = 594
#yPoint3 = 65

#xPoint4 = 271
#yPoint4 = 9
xPoint = []
yPoint = []
count = 0
with picamera.PiCamera() as camera:
#camera = PiCamera()
    #camera.start_preview()

    try:
        camera.resolution = (400, 400)
        camera.framerate = 32
        #stream = io.BytesIO()
        rawCapture = PiRGBArray(camera, size=(400, 400))

        time.sleep(2)

        #Create old frame
        for frames in camera.capture_continuous(rawCapture, format="rgb", use_video_port=True):
            lcd.clear()
            lcd2.clear()
            #print(frame)
            frame = frames.array
            #frame = np.asarray(frames)
            old_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            #stream.truncate()
            #stream.seek(0)
            rawCapture.truncate()
            rawCapture.seek(0)
            break

        # Lucas Kanade params
        lk_params = dict(winSize = (15, 15), maxLevel = 4,
                         criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

        # Mouse function
        
        def select_point(event, x, y, flags, params):
            global point, point_selected, old_points, count, xPoint, yPoint
            if event == cv2.EVENT_LBUTTONDOWN:
                point = (x, y)
                if count <= 3:
                    xPoint.append(x)
                    yPoint.append(y)
                    count += 1

                #if(count > 3):
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
            first_level = cv2.pyrDown(frame)
            second_level = cv2.pyrDown(first_level)
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if point_selected is True:
                cv2.circle(frame, point, 5, (0,0,255), 2)
                new_points, status, error = cv2.calcOpticalFlowPyrLK(old_gray, gray_frame, old_points, None, **lk_params)
                old_gray = gray_frame.copy()
                old_points = new_points
                x, y = new_points.ravel()
                if(count > 3):
                    xRange = abs(xPoint[0] - xPoint[1])
                    yRange = abs(yPoint[0] - yPoint[2])
                    xMap = (round(xRange/80))*5
                    yMap = (round(yRange/80))*5
                    xNew = round(abs(x-xPoint[0]))
                    yNew = round(abs(y-yPoint[0]))
                    posX = xNew % xMap
                    posY = yNew % yMap

                    #posX = math.floor((abs(x-xPoint[0])/abs(xPoint[0] - xPoint[1]))*xMap)
                    #posY = math.floor((abs(y-yPoint[0])/abs(yPoint[0] - yPoint[2]))*yMap)

                    #lcd.write_string(str (posX))
                    #print("\nx:",x)
                    #print("\n y:", y)
                
                    #lcd.write_string(str(x))
                    #lcd2.write_string(str(y))
                    #print("X: ",xPoint, "\t Y: ",yPoint)
                    #print("\nX: ", x, "Y: ", y)
                    if(posX > 15):
                        posX = 15
                    if(posY > 15):
                        posY = 15
                    if count == 4:
                        count = 5
                        initialX = posX
                        initialY = posY
                    print("POSX: ",posX, "\t POSY: ",posY)
                    lcd.cursor_pos = (1,int(initialX))
                    arrow = (0,4,14,31,4,4,4,4)
                    lcd.create_char(0,arrow)
                    lcd.cursor_pos = (0,int(posX))
                    lcd2.cursor_pos = (1,int(initialY))
                    lcd.create_char(0,arrow)
                    lcd2.cursor_pos = (0,int(posY))

                #time.sleep(5)
                
                cv2.circle(frame, (x, y), 5, (0,255,0), -1)

            cv2.imshow("Frame", frame)
            #cv2.imshow("First level", first_level)
            #cv2.imshow("Second level", second_level)

            key = cv2.waitKey(1)
            #stream.truncate()
            #stream.seek(0)
            rawCapture.truncate()
            rawCapture.seek(0)
            if key == ord("q"):
                break

        #camera.release()
        cv2.destroyAllWindows()

    finally:
        #camera.stop_preview()
        print("Stopped")