import paho.mqtt.client as mqtt 
# MQTT callback functions 
def on_connect(client, userdata, flags, rc): 
    print("Connected with result code " + str(rc)) 
    client.subscribe("command/start") 
    client.subscribe("command/terminate") 
    
def on_message(client, userdata, msg): 
    if msg.topic == "command/start": 
        # Start process based on the command received 
        pass
    elif msg.topic == "command/terminate": 
        # Terminate process based on the command received 
        pass
# Initialize the MQTT client
client = mqtt.Client(client_id = "aaron") 
client.on_connect = on_connect 
client.on_message = on_message 
client.connect("192.168.0.248", 1883, 120) 
client.loop_start() 