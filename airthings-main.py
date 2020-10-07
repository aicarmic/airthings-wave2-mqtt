# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from paho.mqtt import client as mqtt_client
import bluepy.btle as btle
import time
import datetime
import argparse
import signal
import struct
import sys
import json

#AIRWAVE CONFIGURATION
serial_number = #Wave2 serial
mac_addr = #Wave2 mac address
data_interval = #fetch interval in seconds

#MQTT CONFIGURATION
broker = #MQTT broker IP in format: '192.168.1.10'
port = 1883
topic = #MQTT topic in format: "basement/airthings"
client_id = #MQTT client, any string
mqtt_user = #MQTT username, optional
mqtt_password = #MQTT password, optional
latest_values = []

#MQTT CONNECTION
def connect_mqtt():
    client = mqtt_client.Client(client_id)
    client.connected_flag=True
    #client.on_connect = on_connect
    print("connecting to MQTT Broker...")
    client.connect(broker, port)
    client.username_pw_set(username=mqtt_user,password=mqtt_password)
    return client

#READ AIRWAVE CLASS
class Wave2():

    CURR_VAL_UUID = btle.UUID("b42e4dcc-ade7-11e4-89d3-123b93f75cba")

    def __init__(self, serial_number):
        self._periph = None
        self._char = None
        self.mac_addr = mac_addr
        self.serial_number = serial_number

    def is_connected(self):
        try:
            return self._periph.getState() == "conn"
        except Exception:
            return False

    def discover(self):
        scan_interval = 0.1
        timeout = 3
        scanner = btle.Scanner()
        for _count in range(int(timeout / scan_interval)):
            advertisements = scanner.scan(scan_interval)
            for adv in advertisements:
                if self.serial_number == _parse_serial_number(adv.getValue(btle.ScanEntry.MANUFACTURER)):
                    return adv.addr
        return None

    def connect(self, retries=1):
        tries = 0
        while (tries < retries and self.is_connected() is False):
            tries += 1
            if self.mac_addr is None:
                self.mac_addr = self.discover()
            try:
                self._periph = btle.Peripheral(self.mac_addr)
                self._char = self._periph.getCharacteristics(uuid=self.CURR_VAL_UUID)[0]
            except Exception:
                if tries == retries:
                    raise
                else:
                    pass

    def read(self):
        rawdata = self._char.read()
        return CurrentValues.from_bytes(rawdata)

    def disconnect(self):
        if self._periph is not None:
            self._periph.disconnect()
            self._periph = None
            self._char = None

class CurrentValues():

    def __init__(self, humidity, radon_sta, radon_lta, temperature):
        self.humidity = humidity
        self.radon_sta = radon_sta
        self.radon_lta = radon_lta
        self.temperature = temperature

    @classmethod
    def from_bytes(cls, rawdata):
        data = struct.unpack("<4B8H", rawdata)
        if data[0] != 1:
            raise ValueError("Incompatible current values version (Expected 1, got {})".format(data[0]))
        return cls(data[1]/2.0, data[4], data[5], data[6]/100.0)

    def __str__(self):
       msg = '{{"Humidity": "{}",'.format(self.humidity)
       msg += '"Temperature": "{}",'.format(self.temperature)
       msg += '"RadonSTA": "{}",'.format(self.radon_sta)
       msg += '"RadonLTA": "{}"}}'.format(self.radon_lta)
       return msg

def _parse_serial_number(manufacturer_data):
    try:
        (ID, SN, _) = struct.unpack("<HLH", manufacturer_data)
    except Exception:  # Return None for non-Airthings devices
        return None
    else:  # Executes only if try-block succeeds
        if ID == 0x0334:
            return SN

def _main():
    wave2 = Wave2(serial_number)
    client = connect_mqtt()
    client.loop_start() 

    def _signal_handler(sig, frame):
        wave2.disconnect()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    timestamp = datetime.datetime.now()
    wave2.connect(retries=3)
    current_values = wave2.read()
    message = str(current_values)
    result = client.publish(topic, message)
    status = result[0]
    if status == 0:
        print(f"{timestamp}: Sent `{message}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")
    client.disconnect()

if __name__ == "__main__":
    _main()
