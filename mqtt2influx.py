import configparser
import json
import sys
import inspect
import queue
import threading

import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from handler import Handler
import handlers


class WffMqttManager:
    def __init__(self, ini_file) -> None:
        self.config = configparser.ConfigParser()
        self.config.read(ini_file)

        print(f"Read {ini_file}")

        self.influx = InfluxDBClient(url=self.config['INFLUXDB']['InfluxDbHost'], token=self.config['INFLUXDB']['Token'], org=self.config['INFLUXDB']['Org'])
        self.influx_write = self.influx.write_api(write_options=SYNCHRONOUS)

        print(f"Connected to InfluxDB at {self.config['INFLUXDB']['InfluxDbHost']}")

        print(f"Setting up message handlers")
        # find handlers
        self.handlers = {}
        for name, obj in inspect.getmembers(handlers):
            if inspect.isclass(obj) and issubclass(obj, Handler):
                configSection = obj.getConfigSection()

                if configSection is not None and self.config.has_section(configSection):
                    topic = self.config[configSection]["topic"]
                    short_topic = topic[:1] if topic.endswith("#") else topic

                    self.handlers[short_topic]["handler"] = obj(self.config)
                    self.handlers[short_topic]["topic"] = topic
                    
                    print(f"Added {obj.getName()} for {topic}")

        self.client = mqtt.Client(protocol=mqtt.MQTTv5)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set(self.config['MQTT']['Username'], password=self.config['MQTT']['Password'])
        self.client.connect(self.config['MQTT']['Broker'], int(self.config['MQTT']['Port']), 60)

        self.client.loop_forever()

    def on_connect(self, client, userdata, flags, rc, clientIdentifier):
        print(f"Connected to MQTT broker {self.config['MQTT']['Broker']}:{self.config['MQTT']['Port']} with result code: {str(rc)}")

        print(f"Subscribing to topics:")

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        for topic in self.handlers:
            client.subscribe(topic)
            print(f"{topic}")


    def on_message(self, client, userdata, msg):

        #find handler
        for short_topic in self.handlers:
            if msg.topic.starts_with(short_topic):
                try:
                    data_point = self.handlers[short_topic].handleMessage(msg)

                    if data_point is not None:
                        self.influx_write.write(bucket=self.config['INFLUXDB']['Bucket'], record=data_point)

                except Exception as e: print(e)


if __name__ == "__main__":
    WffMqttManager(sys.argv[1])