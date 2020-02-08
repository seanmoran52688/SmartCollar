from micropyGPS import MicropyGPS
from machine import UART
from network import LoRa
import socket
import binascii
import struct
import time
import config
import tools

DEBUG = config.DEBUG

speed = config.AUTO
update = config.UPDATE[2] # seconds between update

# Initialize GPS
com = UART(1,pins=(config.TX, config.RX),  baudrate=9600)
my_gps = MicropyGPS()

# Initialise LoRa in LORAWAN mode.
# Please pick the region that matches where you are using the device:
# Asia = LoRa.AS923
# Australia = LoRa.AU915
# Europe = LoRa.EU868
# United States = LoRa.US915
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.US915)

# create an OTAA authentication parameters
app_eui = ubinascii.unhexlify('70B3D57ED002542F')
app_key = ubinascii.unhexlify('2B03CF573794D648EDB0D2D3E356AE4F')

# join a network using OTAA (Over the Air Activation)
lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)

# wait until the module has joined the network
while not lora.has_joined():
    time.sleep(2.5)
    print('Not yet joined...')

# create a LoRa socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

# set the LoRaWAN data rate
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 3)

# make the socket blocking
# (waits for the data to be sent and for the 2 receive windows to expire)
s.setblocking(True)

# send some data
s.send(bytes([0x01, 0x02, 0x03]))

# make the socket non-blocking
# (because if there's no data received it will block forever...)
s.setblocking(False)

# get any data received (if any...)
data = s.recv(64)
print(data)

while True:
    if my_gps.fix_stat > 0 and my_gps.latitude[0] > 0:
        pycom.rgbled(0x007f700) # green
    if com.any():
        my_sentence = com.readline()
        for x in my_sentence:
            my_gps.update(chr(x))
        if  DEBUG == 1:
            print('Longitude', my_gps.longitude);
            print('Latitude', my_gps.latitude);
            print('UTC Timestamp:', my_gps.timestamp);
            print('Fix Status:', my_gps.fix_stat);
            print('Altitude:', my_gps.altitude);
            print('Horizontal Dilution of Precision:', my_gps.hdop)
            print('Satellites in Use by Receiver:', my_gps.satellites_in_use)
            print('Speed in km/hour:', int(my_gps.speed[2]))
        gps_speed = int(my_gps.speed[2])
        if (my_gps.fix_stat > 0 and my_gps.latitude[0] > 0) or DEBUG == 1:
            gps_array = tools.convert_latlon(my_gps.latitude[0] + (my_gps.latitude[1] / 60), my_gps.longitude[0] + (my_gps.longitude[1] / 60), my_gps.altitude, my_gps.hdop)
            print(gps_array)
            s.send(gps_array)
            s.settimeout(3.0) # configure a timeout value of 3 seconds
            # get any data received (if any...)
            set_speed = -1
            try:
                data = s.recv(1)
                print(data)
                set_speed = int(data[0])
                print("set_speed = " + str(set_speed))
                if (set_speed > -1 and set_speed < 5):
                    speed = set_speed
                    update = config.UPDATE[speed]
                    print("Update interval set to: " + str(update) + " seconds")
                    print("Speed type set to: " + str(speed))
            except socket.timeout:
                # nothing received
                if (DEBUG == 1):
                    print("No RX downlink data received")
            time.sleep(.5)
            pycom.rgbled(0)
            if (speed == config.AUTO):
                if (gps_speed < config.MAXSPEED[1]):
                    speed_type = config.STAT
                elif (gps_speed < config.MAXSPEED[2]):
                    speed_type = config.WALK
                elif (gps_speed < config.MAXSPEED[3]):
                    speed_type = config.CYCLE
                else:
                    speed_type = config.CAR
                update = config.UPDATE[speed_type]
                print("Update interval set to: " + str(update) + " seconds")
                print("Speed type = " + str(speed))
            time.sleep(update - 8.5) # account for all the other sleep commands
        time.sleep(5)
