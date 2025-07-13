import os
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print('Connected with result code', rc)
    client.subscribe('cart/events')

def on_message(client, userdata, msg):
    print('Event', msg.topic, msg.payload.decode())

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(os.getenv('MQTT_HOST', 'localhost'), int(os.getenv('MQTT_PORT', 1883)))
client.loop_forever()
