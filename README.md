# Airthings Wave2 to MQTT (Home Assistant)
Script for pulling readings from an Airthings Wave2 over bluetooth and publishing over MQTT to Home Assistant. Desinged to run on an Rpi3 

<img src="https://user-images.githubusercontent.com/1105554/95281101-a4f73f80-0813-11eb-9099-dcda2347b872.png" width="400">


# Credits & Prior Art

This project was inspired by the following, many thanks to their authors:
- https://github.com/Airthings/wave-reader
- https://github.com/hpeyerl/airthingswave-mqtt


# Prerequisites
1. An Airthings Wave2 radon detector
1. Raspberry Pi 3 Model B or Zero W
1. MQTT broker such as the Home Assistant Mosquito add-on

Note: This project works with Airthings wave2 (gen2) devices only. For wave1, please refer to [this project](https://github.com/hpeyerl/airthingswave-mqtt).

**List of packages and dependencies**
| package        | version     | Comments                            |
|----------------|-------------|-------------------------------------|
| python         | 3           | Tested with python 3.7.3            |
| python3-pip    |             | pip3 for python3                    |
| git            |             | To download this project            |
| bluepy         | 1.3.0       | For bluetooth packet processing     |
| libglib2.0-dev |             | For bluepy module                   |
| paho-mqtt      | 1.5.1       | MQTT client                         |

# Initial Setup
Follow this part of the [Airthings guide](https://github.com/Airthings/wave-reader/blob/master/README.md#setup-raspberry-pi0) to setup and configuring your Rpi with Raspbian.

SSH to your Rpi:
```
$ ssh pi@raspberrypi.local
```

If you don't yet have your wave2 SN/Mac, follow the instructions [provided by Airthings here](https://www.airthings.com/resources/raspberry-pi)

Download this project to your Rpi: 
```
git clone https://github.com/aicarmic/airthings-wave2-mqtt
```

Configure the variables in the top of `airthings-main.py` including:
```
serial_number = #Wave2 serial
mac_addr = #Wave2 mac address
data_interval = #fetch interval in seconds
broker = #MQTT broker IP in format: '192.168.1.10'
port = 1883
topic = #MQTT topic in format: "basement/airthings"
client_id = #MQTT client, any string
mqtt_user = #MQTT username, optional
mqtt_password = #MQTT password, optional
```
## Configure MQTT broker
If using Home assistant, install the mosquitto addon and configure a username/password (optional)

Add the following sensors to your HA config. You can change the name and the topic to anything that suits, note that this creates four sensors that each receive on the same topic, so that HA can receive the payload using value templates. Also note that the value template for the Radon latest and Radon average measures convert from `bq/m3` which is how the wave transmits the payload, to `pci/l`:
```
#AIRTHINGS MQTT
  - platform: mqtt
    name: "Airthings Humidity"
    state_topic: "basement/Airthings"
    value_template: '{{value_json.Humidity}}'
    unit_of_measurement: "%"

  - platform: mqtt
    name: "Airthings Temperature"
    state_topic: "basement/Airthings"
    value_template: '{{ (value_json.Temperature | float) | round(1) }}'
    unit_of_measurement: "°C"

  - platform: mqtt
    name: "Radon Latest"
    state_topic: "basement/Airthings"
    value_template: '{{ (value_json.RadonSTA | float / 37) | round(2) }}'
    unit_of_measurement: "pCi/L"

  - platform: mqtt
    name: "Radon Average"
    state_topic: "basement/Airthings"
    value_template: '{{ (value_json.RadonLTA | float / 37) | round(2) }}'
    unit_of_measurement: "pCi/L" 
```
**Optional:** Before restarting HA with the updated config, you can temporarily turn on logging on the MQTT service so you can monitor that the messages are being received successfully:

```
logger:
  default: warning
  logs:
    homeassistant.components.mqtt: debug
```

# Test
Try running the script: `python3 airthngs-main.py`. You should see it connect to your MQTT broker, and if it successfully fetched data from your wave2 you should see output similar to this:
```
connecting to MQTT Broker...
2020-10-07 03:18:54.557063: Sent `{"Humidity": "25.0","Temperature": "21.38","RadonSTA": "84","RadonLTA": "83"}`` to topic `basement/Airthings
```

# Setup as Cron
Once working, you can set this up to run as a cron. On your Rpi, setup the script to run every 15 minutes (or at the desired interval). Note that the data refreshes every 5 minutes (temp/humidity), so no point in fetching at a higher frequency than that:
```
$ sudo crontab -e

# Notice that tasks will be started based on the cron's system
# daemon's notion of time and timezones.
#
# Output of the crontab jobs (including errors) is sent through
# email to the user the crontab file belongs to (unless redirected).
#
# For example, you can run a backup of all your user accounts
# at 5 a.m every week with:
# 0 5 * * 1 tar -zcf /var/backups/home.tgz /home/
#
# For more information see the manual pages of crontab(5) and cron(8)
#
# m h  dom mon dow   command
*/15 * * * * python3 /home/pi/airwave-testing/airwave-testing.py >/dev/null 2>&1
```

# Add your sensors to HA!
Success, you can now add your sensors to HA and/or create automations.
![image](https://user-images.githubusercontent.com/1105554/95281006-7bd6af00-0813-11eb-970e-e8ee6b64a03c.png)

