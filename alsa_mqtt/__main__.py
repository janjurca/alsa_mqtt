import argparse
import logging
import os
import alsaaudio
import sys
from paho.mqtt import client as mqtt_client
import random
import platform


log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def mqtt_connection():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            log.info("Connected to MQTT Broker!")
        else:
            log.error("Failed to connect, return code %d\n", rc)
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
        log.info(f"Send `{value}` to topic `{topic}`")
    else:
        log.info(f"Failed to send message to topic {topic}")


def main():
    global args
    main_parser = argparse.ArgumentParser()
    main_parser.add_argument('--card', action='store', help="Alsa card")
    main_parser.add_argument('--mixer', default="Master", action='store', help="Alsa mixer")
    main_parser.add_argument('--cards', action="store_true", help='Show available alsa cards')
    main_parser.add_argument('--topic', default="homeassistant", action="store", help='MQTT topic path prefix eg: "homeassistant"')
    main_parser.add_argument('--component-name', default="number", action="store", help='MQTT topic component part')
    main_parser.add_argument('--node-id', default=platform.node(), action="store", help='MQTT topic node id part')
    main_parser.add_argument('--broker', default="localhost", action="store", help='MQTT broker address')
    main_parser.add_argument('--port', default=1883, type=int, action="store", help='MQTT port')
    main_parser.add_argument('--username', type=str, action="store", help='MQTT username')
    main_parser.add_argument('--password', type=str, action="store", help='MQTT password')
    main_parser.add_argument('--remove', action="store_true", help='Sends blank config string which removes entity from HASS')

    args = main_parser.parse_args()

    if args.cards:
        scanCards = alsaaudio.cards()
        for card in scanCards:
            log.info("Card:", card)
            log.info("\tMixers:")
            scanMixers = alsaaudio.mixers(scanCards.index(card))
            for mixer in scanMixers:
                log.info(f"\t\t {mixer}")
        exit(0)

    if args.card not in alsaaudio.cards():
        log.info(f"Selected card string ({args.card}) is not within alsa cards list {str(alsaaudio.cards())}.", file=sys.stderr)
        exit(-1)
    if args.mixer not in alsaaudio.mixers(alsaaudio.cards().index(args.card)):
        log.info(f"Selected mixer string ({args.mixer}) is not within alsa mixers for selected card {str(alsaaudio.mixers(alsaaudio.cards().index(args.card)))}.", file=sys.stderr)
        exit(-2)

    mixer = alsaaudio.Mixer(args.mixer, cardindex=alsaaudio.cards().index(args.card))

    connection = mqtt_connection()

    topic = f'{args.topic.strip("/")}/{args.component_name.strip("/")}/{args.node_id.strip("/")}/volume/'
    if args.remove:
        publish(connection, topic + "config", '')
        publish(connection, topic + "state", '')
        exit(0)

    publish(connection, topic + "state", mixer.getvolume()[0])
    publish(connection, topic + "config", f'{{"name": "volume", "min":0, "max":100, "device_class": "number", "command_topic": "{topic}set", "state_topic": "{topic}state"}}')

    def on_message(client, userdata, msg):
        log.info(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        if msg.topic == topic + "set":
            volume = max(0, min(100, int(msg.payload.decode())))
            mixer.setvolume(volume)
            publish(connection, topic + "state", mixer.getvolume()[0])

    connection.subscribe(topic + "set")
    connection.on_message = on_message
    connection.loop_forever()


if __name__ == '__main__':
    main()
