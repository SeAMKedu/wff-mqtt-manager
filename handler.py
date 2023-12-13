from enum import Enum


Database = Enum('Database', ['INFLUXDB', 'MONGODB'])

class Handler:


    def getName():
        return None


    def getConfigSection():
        return None


    def getDatabase(self) -> Database:
        return None


    def getBucket(self):
        return None


    def getCollection(self):
        return None


    def handleMessage(self, msg):
        pass
