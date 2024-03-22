from mqtt_as import MQTTClient, config
import asyncio
from settings import SSID, password, BROKER
import dht, machine

d = dht.DHT22(machine.Pin(13))
# Local configuration
config['server'] = BROKER  # Change to suit
config['ssid'] = SSID
config['wifi_pw'] = password

async def messages(client):  # Respond to incoming messages
    async for topic, msg, retained in client.queue:
        print(f'Topic: "{topic.decode()}" Message: "{msg.decode()}" Retained: {retained}')

async def up(client):  # Respond to connectivity being (re)established
    while True:
        await client.up.wait()  # Wait on an Event
        client.up.clear()
        await client.subscribe('topico/temperatura', 1)  # renew subscriptions
        await client.subscribe('topico/humedad', 1)  # renew subscriptions

async def main(client):
    await client.connect()
    for coroutine in (up, messages):
        asyncio.create_task(coroutine(client))

    while True:
        try:
            d.measure()
            try:
                temperatura=d.temperature()
                await client.publish('topico/temperatura', '{}'.format(temperatura), qos = 1)
            except OSError as e:
                print("sin sensor temperatura")
            try:
                humedad=d.humidity()
                await client.publish('topico/humedad', '{}'.format(humedad), qos = 1)
            except OSError as e:
                print("sin sensor humedad")
        except OSError as e:
            print("sin sensor")
        await asyncio.sleep(10) 

config["queue_len"] = 1  # Use event interface with default queue size
MQTTClient.DEBUG = False  # Optional: print diagnostic messages
client = MQTTClient(config)
try:
    asyncio.run(main(client))
finally:
    client.close()  # Prevent LmacRxBlk:1 errors