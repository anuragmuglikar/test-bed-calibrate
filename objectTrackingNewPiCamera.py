import cv2
import numpy as np
from picamera.array import PiRGBArray
#from picamera import PiCamera
import picamera
import time
import io
from RPLCD.i2c import CharLCD

lcd = CharLCD('MCP23008', 0x24)
lcd.write_string('Hello')

lcd2 = CharLCD('MCP23008', 0x20)
lcd2.write_string('world')


with picamera.PiCamera() as camera:
#camera = PiCamera()
    #camera.start_preview()

    try:
        camera.resolution = (640, 480)
        camera.framerate = 32
        #stream = io.BytesIO()
        rawCapture = PiRGBArray(camera, size=(640, 480))

        time.sleep(2)

        #Create old frame
        for frames in camera.capture_continuous(rawCapture, format="rgb", use_video_port=True):
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
            global point, point_selected, old_points
            if event == cv2.EVENT_LBUTTONDOWN:
                point = (x, y)
                point_selected = True
                old_points = np.array([[x, y]], dtype=np.float32)


        cv2.namedWindow("Frame")
        cv2.setMouseCallback("Frame", select_point)
        point_selected = False
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