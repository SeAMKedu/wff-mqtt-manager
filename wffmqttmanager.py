import configparser
import sys
import os
import importlib
import inspect

import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from pymongo import MongoClient, monitoring
from pymongo.event_loggers import ServerLogger

from handler import Handler, Database


class WffMqttManager:


    def __init__(self, ini_file) -> None:
        self.config = configparser.ConfigParser()
        self.config.read(ini_file)
        print(f"Read {ini_file}")

        print(f"Setting up database connections")
        self.databases = {}
        if self.config.has_section('INFLUXDB'):
            try:
                self.influx = InfluxDBClient(url=self.config['INFLUXDB']['InfluxDbHost'], token=self.config['INFLUXDB']['Token'], org=self.config['INFLUXDB']['Org'])
                self.influx_write = self.influx.write_api(write_options=SYNCHRONOUS)
                self.databases[Database.INFLUXDB] = True
                print(f"Connected to InfluxDB at {self.config['INFLUXDB']['InfluxDbHost']}")
            except Exception as e: 
                self.databases[Database.INFLUXDB] = False
                print(e)

        if self.config.has_section('MONGODB'):
            try:
                monitoring.register(ServerLogger())

                mongo = MongoClient(self.config['MONGODB']['Hostname'],
                            username=self.config['MONGODB']['Username'],
                            password=self.config['MONGODB']['Password'],
                            authSource=self.config['MONGODB']['AuthenticationDatabase'],
                            authMechanism=self.config['MONGODB']['AuhtMechanism'])


                self.mongodb = mongo[self.config['MONGODB']['Database']]
                self.databases[Database.MONGODB] = True
                print(f"Connected to MongoDB at {self.config['MONGODB']['Hostname']}")
            except Exception as e: 
                self.databases[Database.MONGODB] = False
                print(e)

        print(f"Setting up message handlers")
        self.handlers = self.find_handlers()

        self.client = mqtt.Client(protocol=mqtt.MQTTv5)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set(self.config['MQTT']['Username'], password=self.config['MQTT']['Password'])
        self.client.connect(self.config['MQTT']['Broker'], int(self.config['MQTT']['Port']), 60)

        self.client.loop_forever()


    def find_handlers(self):
        handlers = []
        handler_directory = "./handlers"
        for filename in os.listdir(handler_directory):
            if filename.endswith(".py"):
                module_name, file_extension = os.path.splitext(filename)
                module = importlib.import_module(f"handlers.{module_name}")

                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, Handler) and obj != Handler:
                        instance = obj(self.config)
                        # check that necessary database has been initialized
                        if self.databases[instance.getDatabase()] and self.config.has_section(instance.getConfigSection()):
                            print(f"{instance.getName()}")
                            handlers.append(instance)

        return handlers


    def on_connect(self, client, userdata, flags, rc, clientIdentifier):
        print(f"Connected to MQTT broker {self.config['MQTT']['Broker']}:{self.config['MQTT']['Port']} with result code: {str(rc)}")

        print(f"Subscribing to topics:")

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        for handler in self.handlers:
            client.subscribe(handler.topic)
            print(f"{handler.topic}")


    def on_message(self, client, userdata, msg):
        #find handler
        for handler in self.handlers:
            try:
                if msg.topic.startswith(handler.short_topic):
                    data = handler.handleMessage(msg)

                    if data is not None:
                        match handler.getDatabase():
                            case Database.INFLUXDB:
                                self.influx_write.write(bucket=handler.getBucket(), record=data)
                            case Database.MONGODB:
                                self.mongodb[handler.getCollection()].insert_one(data)
                            case _:
                                print(f"Unknown database, handler: {handler.getName()}")
                    break

            except Exception as e: print(e)


if __name__ == "__main__":
    WffMqttManager(sys.argv[1])