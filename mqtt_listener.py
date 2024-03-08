import paho.mqtt.client as mqtt
import time
import json
import configparser

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("command/start", qos=2)
    client.subscribe("command/terminate", qos=2)
    client.subscribe("config/update", qos=2)

def on_message(client, userdata, msg):
    print("Topic:", msg.topic)
    print(msg.payload, "msg.payload")
    if msg.topic == "command/start":
        # if msg.payload.decode() == "start_command_payload":
        with open("start_flag_mqtt.txt", "w") as f:
            f.write("Received start signal from the server")
    elif msg.topic == "command/terminate":
        # if msg.payload.decode() == "terminate_command_payload":
        with open("terminate_flag_mqtt.txt", "w") as f:
            f.write("Received termination signal from the server")

    elif msg.topic == "config/update":
        # Deserialize the received JSON string into a dictionary
        config_data = json.loads(msg.payload)

        # Update the local config with the received data
        local_config = configparser.ConfigParser()
        local_config.read('config.ini')  # Load existing config
        for section, values in config_data.items():
            if not local_config.has_section(section):
                local_config.add_section(section)
            for key, value in values.items():
                if key != "polar":
                    local_config.set(section, key, value)
                    print("section:",section, "key:",key, "values:", values)

        # Save the updated config to the local config file
        with open("config.ini", "w") as config_file:
            local_config.write(config_file)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("10.68.36.17", 1883, 120)

client.loop_start()

try:
    while True:
        time.sleep(1)  
except KeyboardInterrupt:
    print("Exiting...")
finally:
    client.loop_stop()  # Stop the background thread