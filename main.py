# (C) Copyright Peter Hinch 2017-2019.
# Released under the MIT licence.

# This demo publishes to topic "result" and also subscribes to that topic.
# This demonstrates bidirectional TLS communication.
# You can also run the following on a PC to verify:
# mosquitto_sub -h test.mosquitto.org -t result
# To get mosquitto_sub to use a secure connection use this, offered by @gmrza:
# mosquitto_sub -h <my local mosquitto server> -t result -u <username> -P <password> -p 8883

# Public brokers https://github.com/mqtt/mqtt.github.io/wiki/public_brokers

from mqtt_as import MQTTClient
from mqtt_local import config
from settings import NOMBRE
import uasyncio as asyncio
import ujson as json
import uos as os
import dht, machine, ubinascii, btree

# Constantes
CLIENT_ID = ubinascii.hexlify(machine.unique_id()).decode('utf-8')

TOPIC = "iot/2024/" + CLIENT_ID

MODE_MAN = 'man'
MODE_AUT = 'auto'

PIN_DHT = 13
PIN_RELE = 12
PIN_LED = 27

FT = 0.2 # tiempo de encendido/apagado del led (destello)
FP = 2   # tiempo de sleep principal de funcion led_flash()
FN = 20  # numero de destellos
MP = 5.0 # periodo de monitoreo del sensor

# Objetos globales:
d = dht.DHT22(machine.Pin(PIN_DHT))

rele = machine.Pin(PIN_RELE, machine.Pin.OUT)
rele.value(1) # apagado (activo en bajo)

led = machine.Pin(PIN_LED, machine.Pin.OUT)
led.value(1) # apagado (activo en bajo)

# Variables globales:
params = {
    'temperatura':0.0, # grados Celsius 
    'humedad':0.0,     # %
    'setpoint':25.0,   # grados Celsius
    'periodo':20.0,    # segundos
    'modo':MODE_MAN,   # manual o automatico
    'rele':('off' if rele.value() else 'on') # rele activo en bajo
}
flash = False

# Funciones para base de datos
def storedb(spt, per, mod):
    with open('db','wb') as f:
        db = btree.open(f)

        try:
            db[b'setpoint'] = str(spt).encode()
            db[b'periodo'] = str(per).encode()
            db[b'modo'] = mod.encode()
        except:
            print('Error en los tipos de datos')

        db.flush()
        db.close()

def readdb():
    with open('db','rb') as f:
        db = btree.open(f)

        try:
            spt = float(db[b'setpoint'].decode())
            per = float(db[b'periodo'].decode())
            mod = db[b'modo'].decode()
        except:
            print('Clave/s no encontrada/s')

        db.flush()
        db.close()

    return spt, per, mod

# Funciones generales
def read_dht22():
    try:
        d.measure()
        try:
            params['temperatura'] = d.temperature()
        except OSError as e:
            print("sin sensor temperatura")
        try:
            params['humedad'] = d.humidity()
        except OSError as e:
            print("sin sensor humedad")
    except OSError as e:
        print("sin sensor")

def rele_on():
    rele.value(0)

def rele_off():
    rele.value(1)

def led_on():
    led.value(0)

def led_off():
    led.value(1)   

# Funciones para configuracion del cliente: sub_cb, wifi_han, conn_han
def sub_cb(topic, msg, retained):
    
    global flash
    mod = False

    dtopic = topic.decode()
    dmsg = msg.decode()
    print('Topico = {} -> Valor = {}'.format(dtopic, dmsg))

    if dtopic in ('setpoint','periodo'):
        try:
            params[dtopic] = float(dmsg)
            mod = True
        except ValueError:
            print(f'Error: No se puede asignar el valor "{dmsg}" a "{dtopic}"')

    elif dtopic == 'modo':
        if dmsg.lower() in (MODE_MAN, MODE_AUT):
            params[dtopic] = dmsg.lower()
            mod = True
        else:
            print(f'Error: No se puede asignar "{dmsg}" como modo de operacion')

    elif dtopic == 'rele':
        if params['modo'] == MODE_MAN:
            if dmsg.lower() == 'on':
                rele_on()
                print('Rele ON')
            elif dmsg.lower() == 'off':
                rele_off()
                print('Rele OFF')
            else:
                print(f'Advertencia: Comando de rele invalido: "{dmsg}"')

    elif dtopic == 'destello':
        dmsg = dmsg.lower()
        if dmsg in ('on','off'):
            flash = (dmsg == 'on')
            if flash:
                print('Destello activado')
            else:
                print('Destello desactivado')
        else:
            print(f'El comando "{dmsg}" no es valido para destello')
    
    if mod is True:
        storedb(params['setpoint'],params['periodo'],params['modo'])

async def wifi_han(state):
    print('Wifi is ', 'up' if state else 'down')
    await asyncio.sleep(1)

# If you connect with clean_session True, must re-subscribe (MQTT spec 3.1.2.4)
async def conn_han(client):
    await client.subscribe('setpoint', 1)
    await client.subscribe('periodo', 1)
    await client.subscribe('destello', 1)
    await client.subscribe('modo', 1)
    await client.subscribe('rele', 1)

# Funciones principales: monit, led_flash, main, tasks
async def monit():
    while True:
        read_dht22()

        if params['modo'] == MODE_AUT:
            if params['temperatura'] > params['setpoint']:
                rele_on()
                params['rele'] = 'on'
                print('Rele ON')
            else:
                rele_off()
                params['rele'] = 'off'
                print('Rele OFF')

        await asyncio.sleep(MP)

async def led_flash():
    global flash
    while True:
        if flash is True:
            for n in range(FN):
                led_on()
                await asyncio.sleep(FT)
                led_off()
                await asyncio.sleep(FT)
            flash = False

        await asyncio.sleep(FP)

async def main(client):
    await client.connect()
    await asyncio.sleep(2)  # Give broker time
    
    while True:
        print('Publicando', params)
        await client.publish(f'{TOPIC}', json.dumps(params), qos=1)

        await asyncio.sleep(params['periodo'])  # Broker is slow

async def tasks(client):
    await asyncio.gather(main(client), monit(), led_flash())

# Access Data Base
if 'db' not in os.listdir():
    print('Base de datos NO encontrada. CREANDO NUEVA')
    storedb(params['setpoint'], params['periodo'], params['modo'])
else:
    print('Base de datos encontrada. LEYENDO DATOS')
    try:
        params['setpoint'], params['periodo'], params['modo'] = readdb()
    except:
        print('No se encontraron datos. GENERANDO')
        storedb(params['setpoint'], params['periodo'], params['modo'])

# Define client configuration
config['subs_cb'] = sub_cb
config['connect_coro'] = conn_han
config['wifi_coro'] = wifi_han
config['ssl'] = True

# Set up client
MQTTClient.DEBUG = True  # Optional
client = MQTTClient(config)

try:
    asyncio.run(tasks(client))
finally:
    client.close()
    asyncio.new_event_loop()
