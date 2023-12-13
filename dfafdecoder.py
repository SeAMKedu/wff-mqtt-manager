from datetime import datetime

class FFTBroadcast():
    def __init__(self, id, mac, version, type, scale, frequency, buckets, measurementNumber, rssiDB, dataFormat, parsedAt = datetime.now()):
        self.id = id
        self.mac = mac
        self.version = version
        self.type = type
        self.scale = scale
        self.frequency = frequency
        self.buckets = buckets
        self.measurementNumber = measurementNumber
        self.rssiDB = rssiDB
        self.data_format = dataFormat
        self.parsedAt = parsedAt

    def __str__(self):
        return f"{self.id} {self.mac} {self.version} {self.type} {self.scale} {self.frequency} {self.buckets} {self.measurementNumber} {self.rssiDB} {self.data_format} {self.parsedAt}"

class DfAfDecoder:
    def __init__(self):
        self.versionStart = 1
        self.versionEnd = self.versionStart + 1
        self.typeStart = self.versionEnd
        self.typeEnd = self.typeStart + 1
        self.scaleStart = self.typeEnd
        self.scaleEnd = self.scaleStart + 2
        self.frequencyStart = self.scaleEnd
        self.frequencyEnd = self.frequencyStart + 2
        self.bucketStart = self.frequencyEnd
        self.bucketEnd = self.bucketStart + 16
        self.sequenceStart = self.bucketEnd
        self.sequenceEnd = self.sequenceStart + 1

    def bytestou16(data):
        return data[0] * 256 + data[1]

    def fixed88ToFload(data):
        v = DfAfDecoder.bytestou16(data)
        return v / 256;

    def decode_data(self, clean_data):
        data = bytearray.fromhex(clean_data)

        dataFormat = 0xAF
        
        if data[0] != dataFormat:
            raise Exception("Not DF AF data")
        
        version = data[self.versionStart]
        type = ""
        if data[self.typeStart] == 0:
            type = "X"
        elif data[self.typeStart] == 1:
            type = "Y"
        elif data[self.typeStart] == 2:
            type = "Z"
        else:
            raise Exception("Unknown type")
        
        frequency = DfAfDecoder.bytestou16(data[self.frequencyStart:self.frequencyEnd])

        scale = DfAfDecoder.fixed88ToFload(data[self.scaleStart:self.scaleEnd])

        buckets = [None] * 16
        for i in range(0, 16):
            buckets[i] = data[self.bucketStart + i] / scale

        #measurementNumber = int(data[self.sequenceStart:self.sequenceEnd])
        measurementNumber = 1

        id = 0
        return FFTBroadcast(id, None, version, type, scale, frequency, buckets, measurementNumber, None, dataFormat)

