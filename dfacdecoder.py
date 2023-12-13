from datetime import datetime

class P2PBroadcast:
    def __init__(self, id, mac, p2px, p2py, p2pz, rmsx, rmsy, rmsz, voltage, temperature, seq, dataFormat, parsedAt = datetime.now()):
        self.id = id
        self.mac = mac
        self.p2px = p2px
        self.p2py = p2py
        self.p2pz = p2pz
        self.rmsx = rmsx
        self.rmsy = rmsy
        self.rmsz = rmsz
        self.voltage = voltage
        self.temperature = temperature
        self.seq = seq
        self.data_format = dataFormat
        self.parsedAt = parsedAt

    def __str__(self):
        return f"{self.id} {self.p2px} {self.p2py} {self.p2pz} {self.rmsx} {self.rmsy} {self.rmsz} {self.voltage} {self.temperature} {self.seq} {self.data_format} {self.parsedAt}"


class DfAcDecoder:
    def __init__(self):
        self.versionStart = 1
        self.versionEnd = self.versionStart + 1
        self.P2P_XStart = self.versionEnd
        self.P2P_XEnd = self.P2P_XStart + 2
        self.P2P_YStart = self.P2P_XEnd
        self.P2P_YEnd = self.P2P_YStart + 2
        self.P2P_ZStart = self.P2P_YEnd
        self.P2P_ZEnd = self.P2P_ZStart + 2
        self.RMS_XStart = self.P2P_ZEnd
        self.RMS_XEnd = self.RMS_XStart + 2
        self.RMS_YStart = self.RMS_XEnd
        self.RMS_YEnd = self.RMS_YStart + 2
        self.RMS_ZStart = self.RMS_YEnd
        self.RMS_ZEnd = self.RMS_ZStart + 2
        self.voltageStart = self.RMS_ZEnd + 6
        self.voltageEnd = self.voltageStart + 1
        self.temperatureStart = self.voltageEnd
        self.temperatureEnd = self.temperatureStart + 1
        self.seqStart = self.temperatureEnd
        self.seqEnd = self.seqStart + 2


    def bytestou16(data):
        return data[0] * 256 + data[1]


    def fixed88ToFload(data):
        v = DfAcDecoder.bytestou16(data)
        return v / 256;


    def decode_data(self, clean_data):
        data = bytearray.fromhex(clean_data)

        dataFormat = 0xAC
        
        if data[0] != dataFormat:
            raise Exception("Not DF AC data")
        
        version = data[self.versionStart]

        p2px = DfAcDecoder.bytestou16(data[self.P2P_XStart:self.P2P_XEnd])
        p2py = DfAcDecoder.bytestou16(data[self.P2P_YStart:self.P2P_YEnd])
        p2pz = DfAcDecoder.bytestou16(data[self.P2P_ZStart:self.P2P_ZEnd])
        rmsx = DfAcDecoder.bytestou16(data[self.RMS_XStart:self.RMS_XEnd])
        rmsy = DfAcDecoder.bytestou16(data[self.RMS_YStart:self.RMS_YEnd])
        rmsz = DfAcDecoder.bytestou16(data[self.RMS_ZStart:self.RMS_ZEnd])
        voltage = 1600 + 8 * data[self.voltageStart]
        temperature = data[self.temperatureStart]
        seq = DfAcDecoder.bytestou16(data[self.seqStart:self.seqEnd])
        id = 0
        
        return P2PBroadcast(id, None, p2px, p2py, p2pz, rmsx, rmsy, rmsz, voltage, temperature, seq, dataFormat)

