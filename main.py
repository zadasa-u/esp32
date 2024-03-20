import dht, machine

d = dht.DHT22(machine.Pin(13))
d.measure()
print(f'Temperatura : {d.temperature():.1f} grados Celsius')
print(f'Humedad     : {d.humidity():.1f} %')