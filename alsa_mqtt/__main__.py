import argparse
import logging
import os
import alsaaudio
import sys
from paho.mqtt import client as mqtt_client
import random

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def mqtt_connection():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    # Set Connecting Client ID
    client = mqtt_client.Client(client_id=f'alsa-mqtt-{random.randint(0, 100)}')
    if args.username and args.password:
        client.username_pw_set(args.username, args.password)
    client.on_connect = on_connect
    client.connect(args.broker, args.port)
    return client


def publish(connection, topic, value):
    result = connection.publish(topic, value, retain=True)
    # result: [0, 1]
    status = result[0]
    if status == 0:
        print(f"Send `{value}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")


def main():
    global args
    main_parser = argparse.ArgumentParser()
    main_parser.add_argument('--card', action='store', help="Alsa card")
    main_parser.add_argument('--mixer', default="Master", action='store', help="Alsa mixer")
    main_parser.add_argument('--cards', action="store_true", help='Show available alsa cards')
    main_parser.add_argument('--topic', default="alsa_mqtt", action="store", help='MQTT topic path prefix eg: "/home/livingroom/rpi/" ... tool controlled zone ...')
    main_parser.add_argument('--broker', default="localhost", action="store", help='MQTT broker address')
    main_parser.add_argument('--port', default=1883, type=int, action="store", help='MQTT port')
    main_parser.add_argument('--username', type=str, action="store", help='MQTT username')
    main_parser.add_argument('--password', type=str, action="store", help='MQTT password')

    args = main_parser.parse_args()

    if args.cards:
        scanCards = alsaaudio.cards()
        for card in scanCards:
            print("Card:", card)
            print("\tMixers:")
            scanMixers = alsaaudio.mixers(scanCards.index(card))
            for mixer in scanMixers:
                print(f"\t\t {mixer}")
        exit(0)

    if args.card not in alsaaudio.cards():
        print(f"Selected card string ({args.card}) is not within alsa cards list {str(alsaaudio.cards())}.", file=sys.stderr)
        exit(-1)
    if args.mixer not in alsaaudio.mixers(alsaaudio.cards().index(args.card)):
        print(f"Selected mixer string ({args.mixer}) is not within alsa mixers for selected card {str(alsaaudio.mixers(alsaaudio.cards().index(args.card)))}.", file=sys.stderr)
        exit(-2)

    mixer = alsaaudio.Mixer(args.mixer, cardindex=alsaaudio.cards().index(args.card))

    connection = mqtt_connection()

    topic = args.topic.rstrip("/") + "/volume"
    publish(connection, topic, mixer.getvolume()[0])

    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        if msg.topic == topic:
            volume = max(0, min(100, int(msg.payload.decode())))
            mixer.setvolume(volume)

    connection.subscribe(topic)
    connection.on_message = on_message
    connection.loop_forever()


if __name__ == '__main__':
    main()
