import network

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    print('conectando a la red...')
    wlan.connect('SSID', 'PASSWORD')
    while not wlan.isconnected():
        pass
