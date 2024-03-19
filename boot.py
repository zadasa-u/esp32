import network
from settings import SSID, password

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    print('conectando a la red...')
    wlan.connect(SSID, password)
    while not wlan.isconnected():
        pass
