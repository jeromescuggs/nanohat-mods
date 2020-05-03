#!/usr/bin/env python
#
# BakeBit example for the basic functions of BakeBit 128x64 OLED (http://wiki.friendlyarm.com/wiki/index.php/BakeBit_-_OLED_128x64)
#
# The BakeBit connects the NanoPi NEO and BakeBit sensors.
# You can learn more about BakeBit here:  http://wiki.friendlyarm.com/BakeBit
#
# Have a question about this example?  Ask on the forums here:  http://www.friendlyarm.com/Forum/
#
'''
## License

The MIT License (MIT)

BakeBit: an open source platform for connecting BakeBit Sensors to the NanoPi NEO.
Copyright (C) 2016 FriendlyARM

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

import bakebit_128_64_oled as oled
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import time
import sys
import subprocess
import threading
import signal
import os
import socket
import fcntl
import struct
import datetime

global width
width=128
global height
height=64

global pageCount
pageCount=2
global pageIndex
pageIndex=0
global showPageIndicator
showPageIndicator=False

global pageSleep
pageSleep=120
global pageSleepCountdown
pageSleepCountdown=pageSleep

global disableTimeSeconds
disableTimeSeconds=900
global disableCounter
disableCounter=0

global status
status = "\"enabled\""

global enabledMarkerShownSeconds
enabledMarkerShownSeconds=5
global enabledCounter
enabledCounter=0

oled.init()  #initialze SEEED OLED display
oled.setNormalDisplay()      #Set display to normal mode (i.e non-inverse mode)
oled.setHorizontalMode()

global drawing 
drawing = False

global image
image = Image.new('1', (width, height))
global draw
draw = ImageDraw.Draw(image)
global fontb24
fontb24 = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 24);
global font14 
font14 = ImageFont.truetype('DejaVuSansMono.ttf', 14);
global smartFont
smartFont = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 10);
global fontb14
fontb14 = ImageFont.truetype('DejaVuSansMono-Bold.ttf', 14);
global font11
font11 = ImageFont.truetype('DejaVuSansMono.ttf', 11);

global lock
lock = threading.Lock()

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def draw_page():
    global drawing
    global image
    global draw
    global oled
    global font
    global font14
    global smartFont
    global width
    global height
    global pageCount
    global pageIndex
    global showPageIndicator
    global width
    global height
    global lock
    global pageSleepCountdown
    global disableTimeSeconds
    global disableCounter
    global status
    global enabledMarkerShownSeconds
    global enabledCounter

    lock.acquire()
    is_drawing = drawing
    page_index = pageIndex
    lock.release()

    if is_drawing:
        return

    if disableCounter > 0:
        disableCounter = disableCounter -1

    #if the countdown is zero we should be sleeping (blank the display to reduce screenburn)
    if pageSleepCountdown == 1:
        oled.clearDisplay()
        pageSleepCountdown = pageSleepCountdown - 1
        return

    if pageSleepCountdown == 0:
        return

    pageSleepCountdown = pageSleepCountdown - 1

    lock.acquire()
    drawing = True
    lock.release()

    # Draw a black filled box to clear the image.            
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    # Draw current page indicator
    if showPageIndicator:
        dotWidth=4
        dotPadding=2
        dotX=width-dotWidth-1
        dotTop=(height-pageCount*dotWidth-(pageCount-1)*dotPadding)/2
        for i in range(pageCount):
            if i==page_index:
                draw.rectangle((dotX, dotTop, dotX+dotWidth, dotTop+dotWidth), outline=255, fill=255)
            else:
                draw.rectangle((dotX, dotTop, dotX+dotWidth, dotTop+dotWidth), outline=255, fill=0)
            dotTop=dotTop+dotWidth+dotPadding

    if page_index==0:
        text = time.strftime("%A")
        draw.text((2,2),text,font=font14,fill=255)
        text = time.strftime("%e %b %Y")
        draw.text((2,18),text,font=font14,fill=255)
        text = time.strftime("%X")
        draw.text((2,40),text,font=fontb24,fill=255)
    elif page_index==1:
        # Draw some shapes.
        # First define some constants to allow easy resizing of shapes.
        padding = 2
        top = padding
        bottom = height-padding
        # Move left to right keeping track of the current x position for drawing shapes.
        x = 0
        try:
            IPAddress = get_ip_address('eth0')
        except:
            IPAddress = get_ip()
        cmd = "top -bn1 | grep load | awk '{printf \"CPU Load: %.2f\", $(NF-2)}'"
        CPU = subprocess.check_output(cmd, shell = True )
        cmd = "free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
        MemUsage = subprocess.check_output(cmd, shell = True )
        cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%dGB %s\", $3,$2,$5}'"
        Disk = subprocess.check_output(cmd, shell = True )
        tempI = int(open('/sys/class/thermal/thermal_zone0/temp').read());
        if tempI>1000:
            tempI = tempI/1000
        tempStr = "CPU TEMP: %sC" % str(tempI)
        cmd = "curl -f -s http://127.0.0.1/admin/api.php | jq .dns_queries_today"
        Queries = subprocess.check_output(cmd, shell = True ).strip()
        cmd = "curl -f -s http://127.0.0.1/admin/api.php | jq .ads_blocked_today"
        AdsToday = subprocess.check_output(cmd, shell = True ).strip()
        cmd = "curl -f -s http://127.0.0.1/admin/api.php | jq .ads_percentage_today"
        AdsPercentage = subprocess.check_output(cmd, shell = True ).strip()
        cmd = "curl -f -s http://127.0.0.1/admin/api.php | jq .clients_ever_seen"
        ClientsEver = subprocess.check_output(cmd, shell = True ).strip()
        cmd = "curl -f -s http://127.0.0.1/admin/api.php | jq .unique_clients"
        ClientsUnique = subprocess.check_output(cmd, shell = True ).strip()

        draw.text((x, top+2),       "IP: " + str(IPAddress),  font=smartFont, fill=255)
        draw.text((x, top+2+12),    "Queries: " + str(Queries), font=smartFont, fill=255)
        draw.text((x, top+2+24),    "Blocked: " + str(AdsToday),  font=smartFont, fill=255)
        draw.text((x, top+2+36),    "Percent: " + str(AdsPercentage),  font=smartFont, fill=255)
        draw.text((x, top+2+48),    "Clients: " + str(ClientsUnique),  font=smartFont, fill=255)
    elif page_index==3: #Disable Pi-Hole for some senconds? -- no
        draw.text((2, 2),  'Disable ' + str( int(float(disableTimeSeconds)/60) ) + 'min?',  font=fontb14, fill=255)

        draw.rectangle((2,20,width-4,20+16), outline=0, fill=0)
        draw.text((4, 22),  'Yes',  font=font11, fill=255)

        draw.rectangle((2,38,width-4,38+16), outline=0, fill=255)
        draw.text((4, 40),  'No',  font=font11, fill=0)

    elif page_index==4: #Disable Pi-Hole for some senconds? -- yes
        draw.text((2, 2),  'Disable ' + str( int(float(disableTimeSeconds)/60) ) + 'min?',  font=fontb14, fill=255)

        draw.rectangle((2,20,width-4,20+16), outline=0, fill=255)
        draw.text((4, 22),  'Yes',  font=font11, fill=0)

        draw.rectangle((2,38,width-4,38+16), outline=0, fill=0)
        draw.text((4, 40),  'No',  font=font11, fill=255)

    elif page_index==5:
        cmd = "curl -f -s http://127.0.0.1/admin/api.php | jq .status"
        status = subprocess.check_output(cmd, shell = True ).strip()
        if str(status) == "\"disabled\"":
            enabledCounter = 0
            draw.text((2, 2),  'Disabled',  font=fontb14, fill=255)
            if disableCounter > 0:
                draw.text((2, 20),  str(datetime.timedelta(seconds=disableCounter)),  font=fontb24, fill=255)
                draw.rectangle((2,47,int(float(width-4)*(float(disableCounter)/float(disableTimeSeconds))),47+15), outline=0, fill=255)
        elif str(status) == "\"enabled\"":
            disableCounter = 0
            draw.text((2, 2),  'Enabled',  font=fontb14, fill=255)
            if enabledCounter < enabledMarkerShownSeconds:
                enabledCounter = enabledCounter + 1
            else:
                enabledCounter = 0
                update_page_index(1)
        else:
            draw.text((2, 2),  'Disabled',  font=fontb14, fill=255)

    oled.drawImage(image)

    lock.acquire()
    drawing = False
    lock.release()


def is_showing_disable_msgbox():
    global pageIndex
    lock.acquire()
    page_index = pageIndex
    lock.release()
    if page_index==3 or page_index==4:
        return True
    return False

def update_page_index(pi):
    global pageIndex
    lock.acquire()
    pageIndex = pi
    lock.release()

def receive_signal(signum, stack):
    global pageIndex
    global pageSleepCountdown
    global pageSleep
    global disableTimeSeconds
    global disableCounter
    global status

    if pageSleepCountdown == 0:
        image1 = Image.open('pihole.png').convert('1')
        oled.drawImage(image1)
        time.sleep(0.5)

    pageSleepCountdown = pageSleep #user pressed a button, reset the sleep counter

    lock.acquire()
    page_index = pageIndex
    lock.release()

    #if page_index==5:
    #    return

    if signum == signal.SIGUSR1:
        print 'K1 pressed'
        if is_showing_disable_msgbox():
            if page_index==3:
                update_page_index(4)
            else:
                update_page_index(3)
            draw_page()
        else:
            pageIndex=0
            draw_page()

    if signum == signal.SIGUSR2:
        print 'K2 pressed'
        if is_showing_disable_msgbox():
            if page_index==4:
                cmd = "curl -f -s \"http://127.0.0.1/admin/api.php?disable=" + str(disableTimeSeconds) + "&auth=$(docker exec -i pihole grep -oPi \"(?<=WEBPASSWORD\=).+\" /etc/pihole/setupVars.conf)\" | jq .status"
                status = subprocess.check_output(cmd, shell = True )
                lock.acquire()
                disableCounter=disableTimeSeconds
                lock.release()
                update_page_index(5)
                draw_page()
            else:
                update_page_index(0)
                draw_page()
        else:
            update_page_index(1)
            draw_page()

    if signum == signal.SIGALRM:
        print 'K3 pressed'
        cmd = "curl -f -s http://127.0.0.1/admin/api.php | jq .status"
        status = subprocess.check_output(cmd, shell = True ).strip()
        if str(status) == "\"disabled\"":
            enabledCounter = 0
            update_page_index(5)
            draw_page()
        elif is_showing_disable_msgbox():
            update_page_index(0)
            draw_page()
        else:
            update_page_index(3)
            draw_page()


image0 = Image.open('pihole.png').convert('1')
oled.drawImage(image0)
time.sleep(2)

signal.signal(signal.SIGUSR1, receive_signal)
signal.signal(signal.SIGUSR2, receive_signal)
signal.signal(signal.SIGALRM, receive_signal)

while True:
    try:
        draw_page()

        lock.acquire()
        page_index = pageIndex
        lock.release()

        time.sleep(1)
    except KeyboardInterrupt:
        break
    except IOError:
        print ("Error")
