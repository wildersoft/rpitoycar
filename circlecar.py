import RPi.GPIO as GPIO
from time import sleep
from datetime import datetime

import io
import logging
import os
import picamera
import pygame
import socketserver
from threading import Condition
from http import server
from urllib.parse import urlsplit, parse_qs

file = open("panelcar.html","r")

def getFiles():
    options = ""
    directories = os.listdir(os.getcwd() + "/audio")
    for file in directories:
        options = options + "<option values='" + file + "'>" + file + "</option>"

    return options

files = getFiles()
print(files)

PAGE = file.read()
PAGE = PAGE.replace("$$options$$", files)

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
        query = urlsplit(self.path).query
        params = parse_qs(query)
        print('start')
        print(query)
        print('params')
        print(params)
        action = None
        value = None
        param = None
        if len(params):
            action = params['action'][0]
            value = params['value'][0]
            try:
                param = params['param'][0]
            except:
                param = None
                
        if value != None:
            if value == 'go':
                go()
            elif value == 'run':
                run()
            elif value == 'back':
                back()
            elif value == 'stop':
                stop()
            elif value == 'left':
                left()
            elif value == 'right':
                right()
            elif value == 'blink':
                blinkLeds(ledBlink1)
                blinkLeds(ledBlink2)
            elif value == 'ledOn':
                ledOn(ledBlink1)
                ledOn(ledBlink2)
            elif value == 'ledOff':
                ledOff(ledBlink1)
                ledOff(ledBlink2)
            elif value == 'PlayFile':
                playMusic(param)
            elif value == 'honk':
                playMusic('CarHonk.mp3')
            elif value == 'CatMeow':
                playMusic('CatMeow.mp3')
            elif value == 'CatPurring':
                playMusic('CatPurring.mp3')
            elif value == 'DogBarking':
                playMusic('DogBarking.mp3')
            elif value == 'StopFile':
                stopMusic()

            if action == 'speed':
                speed(float(value))
        elif self.path == '/':
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
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    if GPIO.input(PIR_PIN):
                        #print ("Movement detected")
                        now = datetime.now()
                        #ledOn(ledBlink1)
                        #ledOff(ledBlink1)
                        #ledOn(ledBlink2)
                        #ledOff(ledBlink2)
                        current_time = now.strftime("%H:%M:%S")
                        print("Movement detected, current time =", current_time)

                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

def getmixerargs():
    pygame.mixer.init()
    freq, size, chan = pygame.mixer.get_init()
    return freq, size, chan

def initMixer():
    BUFFER = 3072  # audio buffer size, number of samples since pygame 1.8.
    FREQ, SIZE, CHAN = getmixerargs()
    pygame.mixer.init(FREQ, SIZE, CHAN, BUFFER)

def playMusic(file):
    initMixer()
    pygame.init()
    pygame.mixer.init()
    pygame.mixer.music.load('audio/' + file)
    pygame.mixer.music.play() # note -1 for playing in loops
    #while pygame.mixer.music.get_busy() == True:
        #continue
    #do whatever
    #when ready to stop do:
    #pygame.mixer.music.pause()

def stopMusic():
    pygame.mixer.music.pause()
    pygame.mixer.music.stop()

def honk():
    playMusic('honk')

def stop():
    GPIO.output(left1,GPIO.LOW)
    GPIO.output(left2,GPIO.LOW)
    GPIO.output(right1,GPIO.LOW)
    GPIO.output(right2,GPIO.LOW)
    sleep(1)

def back():
    stop()
    GPIO.output(left1,GPIO.LOW)
    GPIO.output(left2,GPIO.HIGH)
    GPIO.output(right1,GPIO.LOW)
    GPIO.output(right2,GPIO.HIGH)

def go():
    stop()
    GPIO.output(right1,GPIO.HIGH)
    GPIO.output(right2,GPIO.LOW)
    GPIO.output(left1,GPIO.HIGH)
    GPIO.output(left2,GPIO.LOW)

def left():
    GPIO.output(left1,GPIO.HIGH)
    GPIO.output(left2,GPIO.LOW)
    GPIO.output(right1,GPIO.LOW)
    GPIO.output(right2,GPIO.HIGH)
    sleep(1)
    stop()

def right():
    GPIO.output(left1,GPIO.LOW)
    GPIO.output(left2,GPIO.HIGH)
    GPIO.output(right1,GPIO.HIGH)
    GPIO.output(right2,GPIO.LOW)    
    sleep(1)
    stop()

def speed(velocity):
    p.ChangeDutyCycle(50 + velocity)
    p2.ChangeDutyCycle(50 + velocity)

def blink(led,seconds):
    print("LED on")
    GPIO.output(led,GPIO.HIGH)
    sleep(seconds)
    print("LED off")
    GPIO.output(led,GPIO.LOW)
    sleep(1)

def ledOn(led):
    print("LED on")
    GPIO.output(led,GPIO.HIGH)

def ledOff(led):
    print("LED off")
    GPIO.output(led,GPIO.LOW)
    
def blinkLeds(led):
    blink(led,3)
    blink(led,1)
    blink(led,5)
    blink(led,1)
    blink(led,2)

left1 = 19
left2 = 26
en = 16
en2 = 13
right1 = 20
right2 = 21
temp1=1
ledBlink1 = 17
ledBlink2 = 27
#GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

PIR_PIN = 4
GPIO.setup(PIR_PIN, GPIO.IN)

GPIO.setup(left1,GPIO.OUT)
GPIO.setup(left2,GPIO.OUT)
GPIO.setup(right1,GPIO.OUT)
GPIO.setup(right2,GPIO.OUT)
GPIO.setup(en,GPIO.OUT)
GPIO.setup(en2,GPIO.OUT)
GPIO.setup(ledBlink1,GPIO.OUT)
GPIO.setup(ledBlink2,GPIO.OUT)

GPIO.output(left1,GPIO.LOW)
GPIO.output(left2,GPIO.LOW)
GPIO.output(right1,GPIO.LOW)
GPIO.output(right2,GPIO.LOW)

p=GPIO.PWM(en,1000)
p2=GPIO.PWM(en2,1000)
p.start(75)
p2.start(75)

with picamera.PiCamera(resolution='640x480', framerate=24) as camera:
    output = StreamingOutput()
    #Uncomment the next line to change your Pi's Camera rotation (in degrees)
    camera.rotation = 180
    camera.start_recording(output, format='mjpeg')
    try:
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        camera.stop_recording()
        GPIO.cleanup()

