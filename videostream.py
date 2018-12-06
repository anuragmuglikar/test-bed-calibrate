# Web streaming example
# Source code from the official PiCamera package
# http://picamera.readthedocs.io/en/latest/recipes2.html#web-streaming

import io
import picamera
import logging
import socketserver
from threading import Condition
from http import server
from sys import exit
from http.server import HTTPServer, SimpleHTTPRequestHandler

import cv2
import numpy as np
from picamera.array import PiRGBArray
import time
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
point_selected = False
xOldWeb = 0
yOldWeb = 0
x = 0
y = 0
blobDetection = False
firstTime = False
#point,xPoint, yPoint,xInitial,yInitial                

PAGE="""\
<html>
<head>
<title>ESE 519 Final Project</title>
<script language="JavaScript">
function point_it(event){
	pos_x = event.offsetX?(event.offsetX):event.pageX-document.getElementById("pointer_div").offsetLeft;
	pos_y = event.offsetY?(event.offsetY):event.pageY-document.getElementById("pointer_div").offsetTop;
	alert("stream.mjpg?x="+ pos_x + "&y=" + pos_y);
    document.getElementById("vid").src = "stream.mjpg?x="+ pos_x + "&y=" + pos_y;
}
</script>
</head>
<body>
<form>
    <center><h1>ESE 519 Final Project</h1></center>
    <div id="pointer_div" onclick="point_it(event)" style = 'width:"640";height:"480"'>
        <center><img src="stream.mjpg?x=0&y=0" id="vid"></center>
    </div>
</form>
</body>
</html>
"""

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        global xOldWeb,yOldWeb,x,y,firstTime,blobDetection,point_selected,old_points,count,xmax,xmin,ymax,ymin
        
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path.startswith("/stream.mjpg"): #== '/stream.mjpg?x=0&y=0':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            i = 0
            data = self.path.split('?')
            data = data[1].split('&')
            x = data[0].split('=')[1]
            x = int(x)
            y = data[1].split('=')[1]
            y = int(y)
            if(xOldWeb != x and yOldWeb != y):
                point_selected = True
                xInitial = x
                yInitial = y
                old_points = np.array([[x, y]], dtype=np.float32)
            # try:
            point = (x, y)
            
            img = output.frame
            frame = cv2.imdecode(np.frombuffer(output.frame, np.uint8), -1)
            old_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Lucas Kanade params
            lk_params = dict(winSize = (15, 15), maxLevel = 4,
                criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))     
            while True:
                with output.condition:
                    output.condition.wait()
                    global blobDetection
                    #old_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    if blobDetection == False:
                        detector = cv2.SimpleBlobDetector_create()
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

                self.wfile.write(b'--FRAME\r\n')
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Content-Length', len(img))
                self.end_headers()
                self.wfile.write(img)
                self.wfile.write(b'\r\n')
                
                    
            # except Exception as e:
            #     logging.warning(
            #         'Removed streaming client %s: %s',
            #         self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
    output = StreamingOutput()
    #Uncomment the next line to change your Pi's Camera rotation (in degrees)
    #camera.rotation = 90
    camera.start_recording(output, format='mjpeg')
    try:
        print("Starting server...")
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()