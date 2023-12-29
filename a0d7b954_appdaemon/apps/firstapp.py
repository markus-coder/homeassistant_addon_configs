import hassapi as hass
import datetime
import json
import paho.mqtt.client as mqtt
import serial
from dataclasses import dataclass


# Release Notes
#
# Version 1.0:
#   Initial Version


class FirstApp(hass.Hass):
    VitodensCommands = [0x0800, 2 ,10, "vitocontrol/AussentemperaturSensor1", "temperature"],\
        [0x0802, 2 ,10, "vitocontrol/KesseltemperaturSensor3", "temperature"],\
        [0x0804, 2 ,10, "vitocontrol/SpeichertemperaturSensor5", "temperature"],\
        [0x0806, 2 ,10, "vitocontrol/Speichertemperatur2Sensor5B", "temperature"],\
        [0x080A, 2 ,10, "vitocontrol/Ruecklauftemperatur17A", "temperature"],\
        [0x080C, 2 ,10, "vitocontrol/Vorlauftemperatur17B", "temperature"],\
        [0x0950, 2 ,10, "vitocontrol/VorlauftemperaturAnlage", "temperature"],\
        [0x5525, 2 ,10, "vitocontrol/AussentemperaturTiefpass", "temperature"],\
        [0x5527, 2 ,10, "vitocontrol/AussentemperaturGedaempft", "temperature"],\
        [0xA202, 2 ,100, "vitocontrol/KesseltemperaturKessel1", "temperature"],\
        [0xA242, 2 ,100, "vitocontrol/KesseltemperaturKessel2", "temperature"],\
        [0x2900, 2 ,10, "vitocontrol/VorlauftemperaturA1M1", "temperature"],\
        [0x3900, 2 ,10, "vitocontrol/VorlauftemperaturM2", "temperature"],\
        [0x4900, 2 ,10, "vitocontrol/VorlauftemperaturM3", "temperature"],\
        [0x0810, 2 ,10, "vitocontrol/KesseltemperaturTiefpass", "temperature"],\
        [0x0812, 2 ,10, "vitocontrol/SpeichertemperaturTiefpass", "temperature"],\
        [0x0814, 2 ,10, "vitocontrol/Speichertemperatur2Tiefpass", "temperature"],\
        [0x0818, 2 ,10, "vitocontrol/Ruecklauftemperatur17ATiefpass", "temperature"],\
        [0x081A, 2 ,10, "vitocontrol/RueckVorlauftemperatur17BTiefpass", "temperature"],\
        [0x0896, 2 ,10, "vitocontrol/RaumtemperaturA1M1Tiefpass", "temperature"],\
        [0x0898, 2 ,10, "vitocontrol/RaumtemperaturM2Tiefpass", "temperature"],\
        [0x089A, 2 ,10, "vitocontrol/RaumtemperaturM3Tiefpass", "temperature"],\
        [0x5600, 2 ,10, "vitocontrol/VorlaufsolltemperaturAnlage", "temperature"],\
        [0x2544, 2 ,10, "vitocontrol/VorlaufsolltemperaturA1M1", "temperature"],\
        [0x3544, 2 ,10, "vitocontrol/VorlaufsolltemperaturM2", "temperature"],\
        [0x4544, 2 ,10, "vitocontrol/VorlaufsolltemperaturM3", "temperature"],\
        [0x56A0, 2 ,10, "vitocontrol/RuecklaufsolltemperaturAnlage", "temperature"],\
        [0xA226, 2 ,100, "vitocontrol/KesselsolltemperaturKessel1", "temperature"]

    def initialize(self):
        self.log("firstapp staring", level="INFO")

        time = datetime.time(0, 0, 0)
        #self.run_minutely(self.printlog, time)
        self.run_every(self.printlog, "now", 10 * 60)

    def printlog(self, kwargs):
        self.log("getting data")
        self.client = mqtt.Client()
        self.client.username_pw_set("admin", "admin")
        self.client.connect("192.168.178.106", 1883,60)
       
        self.ser = serial.Serial('/dev/ttyUSB0', 4800, timeout=0, stopbits=2, parity=serial.PARITY_EVEN)
        self.ser.timeout = 3
        
        self.vitodens_reset_mode()
        if self.vitodens_init_command_mode():
            i = 0
            for x in self.VitodensCommands:
                #self.log(x)
                self.vitodens_read(i)
                i = i + 1
            self.vitodens_exit_command_mode()
        self.vitodens_shutdown()

    def vitodens_reset_mode(self):
        #global state 
        self.log("vitodens_reset_mode")
        
        c = self.ser.read(1)
        if(c == b'\x05'):
            self.log("if: start gefunden") 
            #print("start gefunden")
            #state = State().vitodens_init_command_mode
            return
        else:
            #self.log("kein start gefunden")    
            myarray = bytearray().fromhex("04")      
            i = 0
            while i < 5:
                self.ser.write(myarray)
                i = i + 1
                c = self.ser.read(1)
                #self.log(c)
                self.log("vitodens_reset_mode wait for 0x05 retry")
                if(c == b'\x05'):
                    self.log("start gefunden")
                    #state = State().vitodens_init_command_mode
                    return

    def vitodens_init_command_mode(self):
        self.log("vitodens_init_command_mode")

        c = self.ser.read(1)
        #self.log(c)
        i = 0
        while i < 3:
            if(c == b'\x05'):
                self.log("ICM 0x5")    
                #return False
            
            #time.sleep(2.0)
            #c = self.ser.flush()
            myarray = bytearray().fromhex("16 00 00")       
            self.ser.write(myarray)
            i = i + 1
            c = self.ser.read(1)
            self.log(c)
            if(c == b'\x06'):
                global state 
                self.log("command mode")
                #state = State().vitodens_read_device_type
                return True
        self.log("Init Command Mode False")
        return False
        
    def vitodens_read(self, position):
        address, retValLenght, retValFactor, mqttTopic, valueKey = self.VitodensCommands[position]
        #self.log("vitodens_read " + mqttTopic + " " + str(retValFactor))
        #myarray = bytearray().fromhex("41 05 00 01 55 25 02 82")
        # #myarray =  vitoCreateCommand(0x5525, 2) 
        myarray = self.vitoCreateCommand(address, retValLenght)
        self.ser.write(myarray)
        buffer = self.ser.read(11)
        elements = [0, 0]
        temp = bytearray(elements)
        temp[0] = buffer[9]
        temp[1] = buffer[8]
        #self.log(buffer.hex())
        #self.log(temp.hex())
        temp_int = int.from_bytes(temp, byteorder='big') 
        #self.log(mqttTopic + " ohne " + str(temp_int))
        self.log(mqttTopic + " " + str(temp_int/retValFactor))
        
        data = {valueKey: temp_int/retValFactor}
        jsonData = json.dumps(data)
        self.client.publish(mqttTopic, jsonData, qos=0)
        #global state
        #state = State().vitodens_exit_command_mode

    def vitodens_exit_command_mode(self):
        self.log("vitodens_exit_command_mode")
        i = 0 
        self.ser.flush()
        myarray = bytearray().fromhex("04")       
        self.ser.write(myarray)
        while i < 5:
            i = i + 1
            c = self.ser.read(1)
            #self.log(c)
            if(c == b'\x05'):
                self.log("vitodens_exit_command_mode: start gefunden")
                #global state 
                #state = State().vitodens_shutdown
                return
        self.log("kein start gefunden")

    def vitodens_shutdown(self):
        print("vitodens_shutdown")
        self.ser.close()

    def calcCRC(self, buffer):
        crc = 0
        count = buffer[0]
        print(count)
        for i in range(0, buffer[0] + 1):
            crc += buffer[i]
        return crc

    def vitoCreateCommand(self, address, requestedDataSize):
        command = bytearray(8)
        result_len = 0
        flag = 0

        # Building the request payload:
        command[0] = 0x41  # Type of Message: Host -> Vitodens
        command[1] = 0x05  # Read access
        command[2] = 0x00  # Type of Message: Host -> Vitodens
        command[3] = 0x01  # Read access
        command[4] = (address >> 8) & 0xff  # high byte (Address is BIG-ENDIAN!)
        command[5] = address & 0xff  # low byte
        command[6] = requestedDataSize  # Number of requested bytes
        command[7] = self.calcCRC(command[1:7])
        print(command[7])
        
        return command

