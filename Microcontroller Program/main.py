import network
import machine
from machine import Pin, I2C, RTC
import ssd1306
import socket
import time as utime


rtc = RTC()
rtc.datetime((2023, 9, 26, 12, 12, 12, 0, 0))
i2c = I2C(scl=Pin(5), sda=Pin(4))
display = ssd1306.SSD1306_I2C(128, 32, i2c)
led = Pin(0, Pin.OUT)
led.value(1)
display_on = False
show_time = False

def display_time():
    current_time = rtc.datetime()
    display.fill(0)
    time_str = "{:02d}:{:02d}:{:02d}".format(current_time[4], current_time[5], current_time[6])
    display.text(time_str, 0, 16)
    display.show()
    utime.sleep(1)


def connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        # sta_if.connect('Tenda_64AB40', 'C0lumbi@32')
        sta_if.connect('Columbia University', '')
        while not sta_if.isconnected():
            pass
    return sta_if.ifconfig()


ip_addr = connect()
print("ip address")
print(ip_addr)

socket_addr = socket.getaddrinfo(ip_addr[0], 80)[0][-1] #IP address and port 80

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #Object s, Contructor specifying IPv4, TCP
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #Can use again(reusable)

s.bind(socket_addr) #binding

s.listen(1)
s.settimeout(1)
print('listening on', socket_addr)
client = 0
while True:
    try:
        client, addr = s.accept()   #will accept incoming connections from client ('client' is object of actual client)
        print('client connected from', addr) #Contains Client's IP address and port
        request = client.recv(1024) #reads data and stores in request
        request = str(request)
        print('content = ', request)

        # if 'msg' in request:
        #     msg = request.split('/?msg=')[1].split('HTTP')[0]
        #     msg = msg.replace('%20', ' ')


            # resp_msg = msg
        msg = request.lower()
            #Searching for keywords
            # led
        if 'start led' in msg:
            led.value(0)
            print("entered start")
            resp_msg = "start led"
        elif 'stop led' in msg:
            led.value(1)
            print("entered stop")
            resp_msg = "stop led"
        # display
        elif 'display on' in msg:
            display_on = True
            print("entered on")
            resp_msg = "turn on the display"
            display.text(msg, 0, 0)
            print("entered here")
            display.show()

        elif 'display off' in msg:
            display_on = False
            show_time = False
            print("entered off")
            resp_msg = "turn off the display"
            display.fill(0)
            display.show()
        
        # show time
        elif 'show time' or 'showtime' in msg:
            # time_digits = msg.split("=")[1].split("-")
            msg = "show time"
            resp_msg = "showing time now"
            print("entered time")
            display_time()
            show_time = True
            

        # if display_on:
        #     display.fill(0)
        #     display.text(msg, 0, 0)
        #     display.show()

        success_resp = "HTTP/1.1 200 OK\r\n\r\n%s" % resp_msg
        client.send(str.encode(success_resp))
        resp_msg = ""
        # else:
        #     fail_resp = "HTTP/1.1 501 Implemented\r\n\r\nPlease attach msg!"
        #     client.send(str.encode(fail_resp))
            

        client.close()


    except:
        if display_on and show_time:
            err = 0
            
    finally:
        if(show_time == True):
            display_time()

        