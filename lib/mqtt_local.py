# mqtt_local.py Local configuration for mqtt_as demo programs.
from sys import platform, implementation
from mqtt_as import config
from machine import Pin
from settings import SSID, PASS, BROKER, MQTT_PORT, MQTT_USER, MQTT_PASS

config['ssid'] = SSID
config['wifi_pw'] = PASS
config['server'] = BROKER
config['port'] = int(MQTT_PORT)
config['user'] = MQTT_USER
config['password'] = MQTT_PASS
 
def ledfunc(pin, active=0):
    pin = pin
    def func(v):
        pin(not v)  # Active low on ESP8266
    return pin if active else func
    
wifi_led = ledfunc(Pin(14, Pin.OUT, value = 0))  # Red LED for WiFi fail/not ready yet
blue_led = ledfunc(Pin(2, Pin.OUT, value = 1))  # Message received