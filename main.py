# (C) Copyright Peter Hinch 2017-2019.
# Released under the MIT licence.

# This demo publishes to topic "result" and also subscribes to that topic.
# This demonstrates bidirectional TLS communication.
# You can also run the following on a PC to verify:
# mosquitto_sub -h test.mosquitto.org -t result
# To get mosquitto_sub to use a secure connection use this, offered by @gmrza:
# mosquitto_sub -h <my local mosquitto server> -t result -u <username> -P <password> -p 8883

# Public brokers https://github.com/mqtt/mqtt.github.io/wiki/public_brokers

# red LED: ON == WiFi fail
# green LED heartbeat: demonstrates scheduler is running.

from mqtt_as import MQTTClient
from mqtt_local import config
import uasyncio as asyncio
import ujson as json
import uos as os
import dht, machine, ubinascii, btree
from settings import BASE_TOPIC # "ejemplo/base/topic/"

# Constantes
UNIQUE_ID = ubinascii.hexlify(machine.unique_id()).decode('utf-8')

TOPIC = BASE_TOPIC + UNIQUE_ID

PIN_DHT = 13
PIN_LED = 14

# Objetos globales:
d = dht.DHT22(machine.Pin(PIN_DHT))
led = machine.Pin(PIN_LED, machine.Pin.OUT)
led.value(1) # led apagado (activo en bajo)
PL = 1 # Periodo de lectura del estado del led (segundos)

# Variables globales:
params = {
    'temperatura':0.0, # grados Celsius 
    'humedad':0.0,     # %
    'periodo':30,      # segundos
    'led':'off' if led.value() else 'on'
}

# Funciones para base de datos
def storedb(per):
    with open('db','wb') as f:
        db = btree.open(f)

        try:
            db[b'periodo'] = str(per).encode()
        except:
            print('Error en los tipos de datos')

        db.flush()
        db.close()

def readdb():
    with open('db','rb') as f:
        db = btree.open(f)

        try:
            per = float(db[b'periodo'].decode())
        except:
            print('Clave/s no encontrada/s')

        db.flush()
        db.close()

    return per

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

# Funciones para configuracion del cliente: sub_cb, wifi_han, conn_han
def sub_cb(topic, msg, retained):

    mod = False

    dtopic = topic.decode()
    dmsg = msg.decode()
    print('Topico = {} -> Valor = {}'.format(dtopic, dmsg))

    dtopic = dtopic.split('/')[-1]

    if dtopic == 'periodo':
        try:
            period = float(dmsg)
            if period < 10.0:
                period = 10.0 # para evitar periodos demasiado bajos
            params[dtopic] = period
            mod = True
        except ValueError:
            print(f'Error: No se puede asignar el valor "{dmsg}" a "{dtopic}"')
    if dtopic == 'orden-led':
        dmsg = dmsg.lower() # asegurar que el mensaje sea uniforme para la comprobacion
        print(f'Mensaje decodificado: {dmsg}')
        if dmsg == 'true':
            led.value(0) # encendido (activo en bajo)
        elif dmsg == 'false':
            led.value(1) # apagado
        
        # actualizar parametro si es necesario
        params['led'] = 'off' if led.value() else 'on'

    if mod is True:
        storedb(params['periodo'])

async def wifi_han(state):
    print('Wifi is ', 'up' if state else 'down')
    await asyncio.sleep(1)

# If you connect with clean_session True, must re-subscribe (MQTT spec 3.1.2.4)
async def conn_han(client):
    await client.subscribe(f'{BASE_TOPIC}periodo', 1)
    await client.subscribe(f'{BASE_TOPIC}orden-led',1)

# Funciones principales: main
async def main(client):
    #await client.connect()
    #await asyncio.sleep(2)
    
    while True:
        print("main()")
        read_dht22()

        print('Publicando parametros: ', params)
        await client.publish(f'{TOPIC}', json.dumps(params), qos=1)

        await asyncio.sleep(params['periodo'])

async def led_status(client):
    valor_anterior = led.value()
    while True:
        print("led_status()")
        if led.value() != valor_anterior:
            # enviar estado actual del led (True: encendido, False: apagado)
            respuesta = f'{not led.value()==1}'.lower()
            print(f'Publicando estado del led: {respuesta}')
            await client.publish(f'{BASE_TOPIC}respuesta-led',f'{respuesta}',qos=1)
            valor_anterior = led.value()
        await asyncio.sleep(PL)

async def tasks(client):
    await client.connect()
    await asyncio.sleep(2)
    await asyncio.gather(main(client), led_status(client))

# Access Data Base
if 'db' not in os.listdir():
    print('Base de datos NO encontrada. CREANDO NUEVA')
    storedb(params['periodo'])
else:
    print('Base de datos encontrada. LEYENDO DATOS')
    try:
        params['periodo'] = readdb()
    except:
        print('No se encontraron datos. GENERANDO')
        storedb(params['periodo'])

# Define client configuration
config['subs_cb'] = sub_cb
config['connect_coro'] = conn_han
config['wifi_coro'] = wifi_han
config['ssl'] = True

# Set up client
MQTTClient.DEBUG = True  # Optional
client = MQTTClient(config)

try:
    print("Iniciando tareas")
    asyncio.run(tasks(client))
finally:
    client.close()
    asyncio.new_event_loop()