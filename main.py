# Germán Andrés Xander 2023

from machine import Pin
import time

print("esperando pulsador")

sw = Pin(23, Pin.IN)
led = Pin(2, Pin.OUT)
contador=0
bandera=True

while True:
    if sw.value() and bandera:
        bandera=False
        led.value(not led.value())
        contador += 1
        print(contador)
    elif not sw.value():
        bandera=True
    time.sleep_ms(5)