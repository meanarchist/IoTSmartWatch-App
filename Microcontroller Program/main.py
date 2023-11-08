import network
import machine
from machine import Pin, I2C, RTC, PWM, ADC
import ssd1306
import socket
import time as utime
import urequests as requests
import ujson

class ButtonHandler:
    def __init__(self):
        self.rtc = RTC()
        self.i2c = I2C(scl=Pin(5), sda=Pin(4))
        self.disp = ssd1306.SSD1306_I2C(128, 32, self.i2c)
        self.update_interval = 1  # Every 1 second

    def change_time(self, hours=0, minutes=0, seconds=0):
        current_time = self.rtc.datetime()
        new_time = list(current_time)
        new_time[4] += hours
        new_time[5] += minutes
        new_time[6] += seconds
        self.rtc.datetime(tuple(new_time))

button_press=ButtonHandler()

rtc = RTC()
rtc.datetime((2023, 9, 26, 12, 12, 12, 0, 0))
i2c = I2C(scl=Pin(5), sda=Pin(4))
display = ssd1306.SSD1306_I2C(128, 32, i2c)
led = Pin(0, Pin.OUT)
led.value(1)
display_on = False
show_time = False
update_interval = 1 #Every 1 second
last_time_snapshot = 0

#buttons and button flags declaration
button_A = Pin(12, Pin.IN, Pin.PULL_UP)
last_pressed_A = utime.ticks_ms()
flag_pressed_A = 0
button_B = Pin(13, Pin.IN, Pin.PULL_UP)
last_pressed_B = utime.ticks_ms()
flag_pressed_B = 0
button_C = Pin(14, Pin.IN, Pin.PULL_UP)
last_pressed_C = utime.ticks_ms()
flag_pressed_C = 0
flag_alarm_mode = 0

#alarm detection flags
flag_alarm_mode = 0
alarm_time_set = [0, 0, 0]
alarm_time = [0, 0, 0]

#buzzer
melody = 'cdefgabC'
rhythm = [8, 8, 8, 8, 8, 8, 8, 8]
tempo = 5
tones = {
    'c': 262,
    'd': 294,
    'e': 330,
    'f': 349,
    'g': 392,
    'a': 440,
    'b': 494,
    'C': 523,
    ' ': 0,
}
beeper = PWM(Pin(0, Pin.OUT), freq=440, duty=512)
beeper.deinit()

def display_time():
    current_time = rtc.datetime()
    display.fill(0)
    time_str = "{:02d}:{:02d}:{:02d}".format(current_time[4], current_time[5], current_time[6])
    display.text(time_str, 0, 16)
    display.show()
    utime.sleep(1)

def callbackA(pin):
    global last_pressed_A
    global flag_pressed_A 

    if((utime.ticks_ms() - last_pressed_A) > 100):
        flag_pressed_A = 1
        last_pressed_A = utime.ticks_ms()
    else:
        flag_pressed_A = 0

def callbackB(pin):
    global last_pressed_B
    global flag_pressed_B 
    global flag_alarm_mode

    if((utime.ticks_ms() - last_pressed_B) > 100):
        flag_pressed_B = 1
        last_pressed_B = utime.ticks_ms()
    else:
        flag_pressed_B = 0

def callbackC(pin):
    global last_pressed_C
    global flag_pressed_C 
    global flag_alarm_mode
    global last_time_snapshot
    global alarm_time_set
    global alarm_time
    # if((utime.ticks_ms() - last_pressed_C) > 50 and (utime.ticks_ms() - last_pressed_C) < 150):
    #     if(flag_alarm_mode == 0):
    #         flag_alarm_mode = 1
    #     else:
    #         flag_alarm_mode = 0

    time_diff = (utime.ticks_ms() - last_pressed_C)
    if(time_diff > 300):
        print(time_diff)
        #time edit mode
        if(time_diff > 200 and time_diff < 1200):
            print("Alarm Mode")
            if(flag_alarm_mode == 0):
                last_time_snapshot = rtc.datetime()
                alarm_time[0] = last_time_snapshot[4]
                alarm_time[1] = last_time_snapshot[5]
                alarm_time[2] = last_time_snapshot[6]
                flag_alarm_mode = 1
            else:
                flag_alarm_mode = 0
                alarm_time_set[0] = alarm_time[0]
                alarm_time_set[1] = alarm_time[1]
                alarm_time_set[2] = alarm_time[2]
                rtc.datetime(last_time_snapshot)
                print(last_time_snapshot)
                print(alarm_time_set)

        flag_pressed_C = 1
        last_pressed_C = utime.ticks_ms()
    else:
        flag_pressed_C = 0

    

button_A.irq(trigger=Pin.IRQ_RISING, handler=callbackA)
button_B.irq(trigger=Pin.IRQ_RISING, handler=callbackB)
button_C.irq(trigger=Pin.IRQ_RISING, handler=callbackC)

#Brighness Change
sensor_pin = 0   #Initialize
sensor = ADC(sensor_pin)

def update_display():
    display.fill(0)    #Clear display/OLED
    current_time = rtc.datetime()
    
    # Display the time on the OLED screen
    if(flag_alarm_mode == 1):
        display.text("Alarm Mode:", 0, 0)
        alarm_time_str = "{:02d}:{:02d}:{:02d}".format(alarm_time[0], alarm_time[1], alarm_time[2])
        display.text(alarm_time_str, 0, 16)
    else:    
        display.text("Current Time:", 0, 0)
        # Format the time as a string
        time_str = "{:02d}:{:02d}:{:02d}".format(current_time[4], current_time[5], current_time[6])
        display.text(time_str, 0, 16)

    # Refresh the display
    #   disp.text(alarm_time_str, 0, 32)
    display.show()
    utime.sleep(update_interval)

def brightness():
    sensor_val = sensor.read()  #0-1024

    brightness_val = int(sensor_val/4)  #0-255

    display.contrast(brightness_val)

def set_alarm_time(hours=0, minutes=0, seconds=0):
        alarm_time[0] += hours
        alarm_time[1] += minutes
        alarm_time[2] += seconds

def get_location():
    lat_log_api = "http://ip-api.com/json"
    latlong_response = requests.get(lat_log_api)
    latlong_data = ujson.loads(latlong_response.text)
    latlong_response.close()
    return latlong_data

def get_weather(lat, lon):
    weather_url = "https://api.openweathermap.org/data/2.5/weather?lat=%s&lon=%s&appid=YOUR_API_KEY" % (lat, lon)
    weather_response = requests.get(weather_url)
    weather_data = ujson.loads(weather_response.text)
    weather_response.close()
    weather = weather_data['weather'][0]['main']
    return weather

def connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('Connecting to network...')
        sta_if.active(True)
        sta_if.connect('Columbia University', '')
        while not sta_if.isconnected():
            pass
    return sta_if.ifconfig()

ip_addr = connect()
print("IP Address:", ip_addr)

socket_addr = socket.getaddrinfo(ip_addr[0], 80)[0][-1]

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

s.bind(socket_addr)
s.listen(1)
s.settimeout(1)
print('Listening on', socket_addr)
client = 0

def alarm_mode():
    update_display()
    brightness()

    if(flag_alarm_mode == 0):
        if flag_pressed_A:
            button_press.change_time(hours=1)  # Increase hours by 1
            flag_pressed_A = 0

        if flag_pressed_B:
            button_press.change_time(minutes=1)  # Increase minutes by 1
            flag_pressed_B = 0

        if flag_pressed_C:
            button_press.change_time(seconds=1)  # Increase seconds by 1
            flag_pressed_C = 0

    if(flag_alarm_mode == 1):
        if flag_pressed_A:
            set_alarm_time(hours=1)  # Increase hours by 1
            flag_pressed_A = 0

        if flag_pressed_B:
            set_alarm_time(minutes=1)  # Increase minutes by 1
            flag_pressed_B = 0

        if flag_pressed_C:
            set_alarm_time(seconds=1)  # Increase seconds by 1
            flag_pressed_C = 0
    time_now = rtc.datetime()
    if(time_now[4] == alarm_time_set[0] and time_now[5] == alarm_time_set[1] and time_now[6] == alarm_time_set[2]):
        print("alarm sound")
        display.fill(0)
        display.text("Alarm On", 0, 16)
        display.show()
        beeper = PWM(Pin(0, Pin.OUT), freq=440, duty=512)
        utime.sleep(3)
        beeper.deinit()

while True:
    try:
        alarm_mode()
        client, addr = s.accept()
        print('Client connected from', addr)
        request = client.recv(1024)
        request = str(request)
        print('Content:', request)

        msg = request.lower()
        resp_msg = ""

        if 'start led' in msg:
            led.value(0)
            resp_msg = "start led"
        elif 'stop led' in msg:
            led.value(1)
            resp_msg = "stop led"
        elif 'display on' in msg:
            display_on = True
            resp_msg = "turn on the display"
            display.text(msg, 0, 0)
            display.show()
        elif 'display off' in msg:
            display_on = False
            show_time = False
            resp_msg = "turn off the display"
            display.fill(0)
            display.show()
        elif 'show time' in msg or 'showtime' in msg:
            msg = "show time"
            resp_msg = "showing time now"
            display_time()
            show_time = True
        elif 'show weather' in msg:
            location_data = get_location()
            lat = location_data['lat']
            lon = location_data['lon']
            location_msg = "Latitude: %.4f\nLongitude: %.4f" % (lat, lon)
            weather_msg = get_weather(lat, lon)
            display.fill(0)
            display.text(location_msg, 0, 0)
            display.text(weather_msg, 0, 16)
            display.show()
            resp_msg = "showing location and weather"

        success_resp = "HTTP/1.1 200 OK\r\n\r\n%s" % resp_msg
        client.send(str.encode(success_resp))
        client.close()
    except:
        if display_on and show_time:
            err = 0
    finally:
        if show_time:
            display_time()



