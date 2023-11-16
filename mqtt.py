import streamlit as st 
import paho.mqtt.publish as mqtt_publish 
import paho.mqtt.client as mqtt 
import configparser
import json
import subprocess
from datetime import datetime
import os
import sys

def load_config(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    return config

def save_config(config, file_path):
    with open(file_path, 'w') as configfile:
        config.write(configfile)
    
def on_connect(client, userdata, flags, rc): 
    print("Connected with result code " + str(rc)) 
# Initialize the MQTT client 
client = mqtt.Client() 
client.on_connect = on_connect 
client.connect("10.68.45.180", 1883, 120) 
# Streamlit HTML content 
highlighted_text = ''' 
<div style="background-color: #f0e68c; padding: 10px; border-radius: 5px;"> 
    If you change the selected toolbox or configs in Nodes' Server, wait a few seconds before you press the buttons 
</div> 
''' 
 
st.markdown(highlighted_text, unsafe_allow_html=True) 
 
# Defining the clickable link in HTML format 
link_html = '<a href="http://10.68.45.180:8502">Enter the Node 1</a>' 
 
# Embedding the clickable link inside the highlighted_server HTML content 
highlighted_server = f''' 
<div style="background-color: #ff0099; padding: 10px; border-radius: 5px;"> 
    {link_html} 
</div> 
''' 
 
# Using Streamlit's markdown to render the HTML content 
st.markdown(highlighted_server, unsafe_allow_html=True) 

# st.write(highlighted_text, unsafe_allow_html=True)
# st.markdown(highlighted_server.format(link), unsafe_allow_html=True)
st.title("Octonet Server")
st.write("Mode 1:")
st.write("Reminder: The center server's configs will not overwrite the configs in all nodes.(Please set the configs in each node)")
if st.button("Mode 1: Start without overwrite"):
    client.publish("command/start", "start_command_payload", qos=2)

if st.button("Mode 1: Terminate"):
    client.publish("command/terminate", "terminate_command_payload", qos=2)

# Load the .ini file
ini_file_path = 'Global_Server_config.ini'
config = load_config(ini_file_path)

# Display the app title and instructions
st.write("Mode 2:")
st.write("Reminder: The center server's configs will overwrite all the configs in all nodes.(Please edit the following configs and then use Mode 2's 'Save and run')")

# Display and edit the [participant] section
st.sidebar.subheader("Participant")
participant_id = st.sidebar.text_input("ID", config.get("participant", "id"))
participant_age = st.sidebar.number_input("Age", value=int(config.get("participant", "age")))
participant_gender = st.sidebar.selectbox("Gender", ["M", "F"], index=["M", "F"].index(config.get("participant", "gender")))
participant_ethnicity = st.sidebar.text_input("Ethnicity", config.get("participant", "ethnicity"))
participant_height = st.sidebar.number_input("Height", value=int(config.get("participant", "height")))
participant_weight = st.sidebar.number_input("Weight", value=int(config.get("participant", "weight")))

# Update the [participant] section with the new values
config.set("participant", "id", participant_id)
config.set("participant", "age", str(participant_age))
config.set("participant", "gender", participant_gender)
config.set("participant", "ethnicity", participant_ethnicity)
config.set("participant", "height", str(participant_height))
config.set("participant", "weight", str(participant_weight))

# Display and edit the [experiment] section
st.sidebar.subheader("Experiment")
experiment_date = st.sidebar.date_input("Date", value=datetime.strptime(config.get("experiment", "date"), "%Y-%m-%d"))
experiment_time = st.sidebar.time_input("Time", value=datetime.strptime(config.get("experiment", "time"), "%H:%M:%S").time())
experiment_condition = st.sidebar.text_input("Condition", config.get("experiment", "condition"))
experiment_group = st.sidebar.text_input("Group", config.get("experiment", "group"))
experiment_illumination_level = st.sidebar.text_input("Illumination Level", config.get("experiment", "illumination_level"))

# Update the [experiment] section with the new values
config.set("experiment", "date", str(experiment_date))
config.set("experiment", "time", str(experiment_time))
config.set("experiment", "condition", experiment_condition)
config.set("experiment", "group", experiment_group)
config.set("experiment", "illumination_level", experiment_illumination_level)

# Display and edit the [task_info] section
st.sidebar.subheader("Task Info")
task_name = st.sidebar.text_input("Task Name", config.get("task_info", "task_name"))
trial_number = st.sidebar.number_input("Trial Number", value=int(config.get("task_info", "trial_number")))

# Update the [task_info] section with the new values
config.set("task_info", "task_name", task_name)
config.set("task_info", "trial_number", str(trial_number))  

# Display and edit the [notes] section
st.sidebar.subheader("Notes")
notes_comments = st.sidebar.text_area("Comments", config.get("notes", "comments"))

# Update the [notes] section with the new values
config.set("notes", "comments", notes_comments)

# Display and edit the [label] section
st.sidebar.subheader("**Label Info**")
activity_options = ["sit", "jump", "dance", "stand", "walk"]  # Add more activities as needed
activity_label = st.sidebar.selectbox("Activity", options=activity_options, index=activity_options.index(config.get("label_info", "activity")))
config.set("label_info", "activity", activity_label)

# Display and edit the [device_settings] section
st.subheader("Device Settings")

# Create columns for each device
col1, col2, col3, col4, col5 = st.columns(5)

# IRA device settings
with col1:
    st.markdown("**IRA**")
    ira_json = json.loads(config.get("device_settings", "ira"))
    ira_port = st.text_input("Port", ira_json["port"])
    ira_baud_rate = st.text_input("Baud Rate", ira_json["baud_rate"])
    ira_data_storage_location = st.text_input("Data Storage Location", ira_json["Data storage location"])
    ira_datatype = st.text_input("IRA_Datatype", ira_json["IRA_Datatype"])

    ira_json["port"] = ira_port
    ira_json["baud_rate"] = ira_baud_rate
    ira_json["Data storage location"] = ira_data_storage_location
    ira_json["IRA_Datatype"] = ira_datatype
    config.set("device_settings", "ira", json.dumps(ira_json))
    # if st.button("Start IRA"):
    #     processes.append(subprocess.Popen(["python", "IRA/IRA.py"], cwd="/home/aiot-mini/code/"))
    #     st.success("IRA process started.")
    
    # # Terminate processes when the "Terminate" button is clicked
    # if st.button("Terminate IRA"):
    #     with open("terminate_ira_flag.txt", "w") as f:
    #         f.write("1")
    #     st.write("Sent termination_ira signal.")
    #     time.sleep(6)  

    #     if os.path.exists("terminate_ira_flag.txt"):
    #         os.remove("terminate_ira_flag.txt")
    #         st.write("IRA modality is ended.")

# Depth camera settings
with col2:
    st.markdown("**Depth Camera**")
    depth_cam_json = json.loads(config.get("device_settings", "depth_cam"))
    depth_cam_resolution = st.text_input("Resolution", depth_cam_json["resolution"])
    depth_cam_depth_format = st.text_input("Depth Format", depth_cam_json["depth_format"])
    depth_cam_color_format = st.text_input("Color Format", depth_cam_json["color_format"])
    depth_cam_depth_fps = st.text_input("Depth FPS", depth_cam_json["depth_fps"])
    depth_cam_color_fps = st.text_input("Color FPS", depth_cam_json["color_fps"])
    depth_cam_data_storage_location = st.text_input("Data Storage Location", depth_cam_json["Data storage location"])
    depth_cam_depth_datatype = st.text_input("Depth_Datatype", depth_cam_json["Depth_Datatype"])
    depth_cam_rgb_datatype = st.text_input("RGB_Datatype", depth_cam_json["RGB_Datatype"])


    
    depth_cam_json["resolution"] = depth_cam_resolution
    depth_cam_json["depth_format"] = depth_cam_depth_format
    depth_cam_json["color_format"] = depth_cam_color_format
    depth_cam_json["depth_fps"] = depth_cam_depth_fps
    depth_cam_json["color_fps"] = depth_cam_color_fps
    depth_cam_json["Data storage location"] = depth_cam_data_storage_location
    depth_cam_json["Depth_Datatype"] = depth_cam_depth_datatype
    depth_cam_json["RGB_Datatype"] = depth_cam_rgb_datatype
    config.set("device_settings", "depth_cam", json.dumps(depth_cam_json))

    # if st.button("Start depthcamera"):
    #     processes.append(subprocess.Popen(["python","DeptCam/deptcam.py"], cwd="/home/aiot-mini/code/"))
    #     st.success("Depthcamera process started.")
    
    # # Terminate processes when the "Terminate" button is clicked
    # if st.button("Terminate depthcamera"):
    #     with open("terminate_depthcam_flag.txt", "w") as f:
    #         f.write("1")
    #     st.write("Sent termination_depthcam signal.")
    #     time.sleep(6)  

    #     if os.path.exists("terminate_depthcam_flag.txt"):
    #         os.remove("terminate_depthcam_flag.txt")
    #         st.write("Depthcamera modality is ended.")

# Seek Thermal settings
with col3:
    st.markdown("**Seek Thermal**")
    seekthermal_json = json.loads(config.get("device_settings", "seekthermal"))
    seekthermal_port = st.text_input("Port", seekthermal_json["port"])
    seekthermal_frame_rate = st.text_input("Frame Rate", seekthermal_json["frame_rate"])
    seekthermal_color_palette = st.text_input("Color Palette", seekthermal_json["color_palette"])
    seekthermal_shutter_mode = st.text_input("Shutter Mode", seekthermal_json["shutter_mode"])
    seekthermal_agc_mode = st.text_input("AGC Mode", seekthermal_json["agc_mode"])
    seekthermal_temperature_unit = st.text_input("Temperature Unit", seekthermal_json["temperature_unit"])
    seekthermal_data_storage_location = st.text_input("Data Storage Location", seekthermal_json["Data storage location"])
    seekthermal_datatype = st.text_input("seekthermal_Datatype", seekthermal_json["seekthermal_Datatype"])

    seekthermal_json["port"] = seekthermal_port
    seekthermal_json["frame_rate"] = seekthermal_frame_rate
    seekthermal_json["color_palette"] = seekthermal_color_palette
    seekthermal_json["shutter_mode"] = seekthermal_shutter_mode
    seekthermal_json["agc_mode"] = seekthermal_agc_mode
    seekthermal_json["temperature_unit"] = seekthermal_temperature_unit
    seekthermal_json["Data storage location"] = seekthermal_data_storage_location
    seekthermal_json["seekthermal_Datatype"] = seekthermal_datatype
    config.set("device_settings", "seekthermal", json.dumps(seekthermal_json))

    # if st.button("Start SeekThermal Camera"):
    #     processes.append(subprocess.Popen(["python","seekcamera-python/runseek/seekcamera-opencv.py"], cwd="/home/aiot-mini/code/"))
    #     st.success("SeekThermal Camera process started.")
    
    # # Terminate processes when the "Terminate" button is clicked
    # if st.button("Terminate SeekThermal Camera"):
    #     with open("terminate_seek_flag.txt", "w") as f:
    #         f.write("1")
    #     st.write("Sent termination_seek signal.")
    #     time.sleep(6)  

    #     if os.path.exists("terminate_seek_flag.txt"):
    #         os.remove("terminate_seek_flag.txt")
    #         st.write("SeekThermal Camera modality is ended.")
# MMWave settings
with col4:
    st.markdown("**MMWave**")
    mmwave_json = json.loads(config.get("device_settings", "mmwave"))
    mmwave_setting1 = st.text_input("Setting 1", mmwave_json["setting1"])
    mmwave_setting2 = st.text_input("Setting 2", mmwave_json["setting2"])
    mmwave_data_storage_location = st.text_input("Data Storage Location", mmwave_json["Data storage location"])
    mmwave_datatype = st.text_input("mmwave_Datatype", mmwave_json["mmwave_Datatype"])

    mmwave_json["setting1"] = mmwave_setting1
    mmwave_json["setting2"] = mmwave_setting2
    mmwave_json["Data storage location"] = mmwave_data_storage_location
    mmwave_json["mmwave_Datatype"] = mmwave_datatype
    
    config.set("device_settings", "mmwave", json.dumps(mmwave_json))

    # if st.button("Start MMWave"):
    #     processes.append(subprocess.Popen(["python","AWR1843-Read-Data-Python-MMWAVE-SDK-3--master/readData_AWR1843.py"], cwd="/home/aiot-mini/code/"))
    #     st.success("MMWave process started.")
    
    # # Terminate processes when the "Terminate" button is clicked
    # if st.button("Terminate MMWave"):
    #     with open("terminate_mmwave_flag.txt", "w") as f:
    #         f.write("1")
    #     st.write("Sent termination_mmwave signal.")
    #     time.sleep(6)  

    #     if os.path.exists("terminate_mmwave_flag.txt"):
    #         os.remove("terminate_mmwave_flag.txt")
    #         st.write("MMWave modality is ended.")

with col5:
    st.markdown("**Polar**")
    polar_json = json.loads(config.get("device_settings", "polar"))
    polar_record_len = st.text_input("Record Length (in seconds)", polar_json["record_len(in_second)"])
    polar_data_storage_location = st.text_input("Data Storage Location", polar_json["Data storage location"])
    polar_datatype = st.text_input("polar_Datatype", polar_json["polar_Datatype"])
    
    
    polar_json["record_len(in_second)"] = polar_record_len
    polar_json["Data storage location"] = polar_data_storage_location
    polar_json["polar_Datatype"] = polar_datatype
    
    
    config.set("device_settings", "polar", json.dumps(polar_json))



if st.button("Mode 2: Overwrite nodes' configs and Run"):
    save_config(config, ini_file_path)
    # Serialize the updated config data into a JSON string
    config_json = json.dumps({section: dict(config.items(section)) for section in config.sections()})
    st.success("All nodes' config files are overwritten.")
    # Publish the JSON string to the MQTT topic
    client.publish("config/update", config_json, qos=2)
    client.publish("command/start", "start_command_payload", qos=2)

if st.button("Mode 2: Terminate "):
    client.publish("command/terminate", "terminate_command_payload", qos=2)


client.loop_start()  