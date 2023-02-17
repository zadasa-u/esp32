from machine import Pin
import time

led = Pin(2, Pin.OUT)
while (True):
    led.on()
    time.sleep(.5)
    led.off()
    time.sleep(.5)
