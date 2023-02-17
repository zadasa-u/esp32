from machine import Pin
import time

led = Pin(2, Pin.OUT)
while (True):
    led.on()
    print("encender")
    time.sleep(.5)
    led.off()
    print("apagar")
    time.sleep(.5)
