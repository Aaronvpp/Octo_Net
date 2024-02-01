import streamlit as st
import configparser
import json
import subprocess
from datetime import datetime
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from log_utils import *
from save_timestamp_data import *
import time
import psutil
import glob
import re
import paho.mqtt.client as mqtt
import threading
import asyncio

PYTHON_EXE = "/home/aiot-mini/anaconda3/envs/octo/bin/python"
print("Startover------------------------------------")
if "start_flag" not in st.session_state:
    print(st.session_state,"st.session_state")
    st.session_state.start_flag = False

if "terminate_flag" not in st.session_state:
    print(st.session_state,"st.session_state")
    st.session_state.terminate_flag = False


if "polar_ready" not in st.session_state:
    st.session_state.polar_ready = False

if "polar_flag" not in st.session_state:
    st.session_state.polar_flag = False
print("finish Flag initialization------------------------------------")
# def on_connect(client, userdata, flags, rc):
#     print("Connected with result code " + str(rc))
#     client.subscribe("command/start")

# def on_message(client, userdata, msg):
#     print(msg.payload,"msg.payload")
#     if msg.payload.decode() == "start_command_payload":
#         st.session_state.start_flag = True
#         print("Setting start_flag to True")
#         st.rerun()

# @st.cache_resource
# def mqtt_loop():
#     client = mqtt.Client()
#     client.on_connect = on_connect
#     client.on_message = on_message
#     client.connect("10.68.89.123", 1883, 120)
#     client.loop_start()
#     return client

# mqtt_client = mqtt_loop()
# client = mqtt.Client()
# client.on_connect = on_connect
# client.on_message = on_message
# client.connect("192.168.0.120", 1883, 120)
# client.loop_start()

def wait_for_polar_ready():
    while not os.path.exists('polar_ready.txt'):
        time.sleep(0.5)
    st.success("Polar device is now ready.")

def check_polar_ready():
    if os.path.exists("polar_ready.txt"):
        st.session_state.polar_flag = True  
        os.remove("polar_ready.txt")
        st.rerun()
        return True
    return False

def check_start_flag():
    if os.path.exists("start_flag_mqtt.txt"):
        st.session_state.start_flag = True  
        os.remove("start_flag_mqtt.txt")
        st.rerun()
        return True
    return False

def check_terminate_flag():
    if os.path.exists("terminate_flag_mqtt.txt"):
        st.session_state.terminate_flag = True  
        os.remove("terminate_flag_mqtt.txt")
        st.rerun()
        return True
    return False

# if "processes" not in st.session_state:
#     st.session_state.processes = []
processes = []
 # Initialize the process_dict
process_dict = {
    "IRA": {"pid": None},
    "Depth Camera": {"pid": None},
    "MMWave": {"pid": None},
    "SeekThermal": {"pid": None},
    "Polar": {"pid": None},
    "Acoustic Recorder": {"pid": None},
    "Acoustic Player": {"pid": None},
    "uwb":{"pid": None},
    "ToF":{"pid": None},
    }
if "process_polar" not in st.session_state:
    st.session_state.process_polar = []
if "process_dict_polar" not in st.session_state:
    st.session_state.process_dict_polar = {
    "Polar": {"pid": None},
    }
# process_dict = {
#     "IRA": {"pid": None},
#     "Depth Camera": {"pid": None},
#     "MMWave": {"pid": None},
#     "SeekThermal": {"pid": None},
#     "Polar": {"pid": None},
#     "Acoustic Recorder": {"pid": None},
#     "Acoustic Player": {"pid": None},
#     "uwb":{"pid": None},
# }

# def update_modality_status(status_placeholder):
#     try:
#         with open(os.path.abspath(os.path.join(os.path.dirname(__file__), "status.json")), "r") as f:
#             status_dict = json.load(f)
#     except json.JSONDecodeError:
#         status_dict = {}  # Provide a default value or log an error message


#     status_text = ""
#     for process_name, status in status_dict.items():
#         if status == 'running' or status == 'sleeping':
#             status_text += f"{process_name}: {status} (Running)\n"
#         else:
#             status_text += f"{process_name}: {status} (Not Running)\n"

#     status_placeholder.text(status_text)
def get_experiment_duration(log_file_path):
    with open(log_file_path, "r") as f:
        lines = f.readlines()

    start_time_match = re.search(r"NTP Time: \[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d{6})\]", lines[0])
    end_time_match = re.search(r"NTP Time: \[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d{6})\]", lines[-1])

    if start_time_match and end_time_match:
        start_time = datetime.strptime(start_time_match.group(1), "%Y-%m-%d %H:%M:%S.%f")
        end_time = datetime.strptime(end_time_match.group(1), "%Y-%m-%d %H:%M:%S.%f")

        # Calculate the duration
        duration = end_time - start_time
        return duration
    else:
        return None



def update_modality_status(status_placeholder):
    ordered_process_names = ["IRA", "Depth Camera", "MMWave", "SeekThermal", "Polar", "Acoustic Recorder", "Acoustic Player", "uwb", "ToF"]
    try:
        with open(os.path.abspath(os.path.join(os.path.dirname(__file__), "status.json")), "r") as f:
            status_dict = json.load(f)
    except json.JSONDecodeError:
        status_dict = {}  # Provide a default value or log an error message

    status_text = ""
    for process_name in ordered_process_names:
        if process_name in status_dict:
            process_info = status_dict[process_name]
            status = process_info["status"]
            color = "green" if status.lower() in ['running', 'sleeping'] else "red"
            status_indicator = f'<span style="color:{color};">⬤</span>'
            sampling_rate_info = f'Actual Sampling rate: {round(process_info["sampling_rate"], 2)}' if "sampling_rate" in process_info else ""
            status_text += f"{status_indicator} {process_name}: {sampling_rate_info} ({'Running' if color == 'green' else 'Not Running'})<br>"
    
    status_placeholder.markdown(status_text, unsafe_allow_html=True)

def find_latest_log_file(log_dir):
    log_files = glob.glob(os.path.join(log_dir, "config_*.log"))
    max_index = -1
    latest_log_file = None

    for log_file in log_files:
        match = re.search(r"config_(\d+).log", log_file)
        if match:
            index = int(match.group(1))
            if index > max_index:
                max_index = index
                latest_log_file = log_file

    if latest_log_file is None:
        print("No log files found in the directory:", log_dir)

    return latest_log_file

def get_process_status(pid):
    try:
        process = psutil.Process(pid)
        return process.status()
    except psutil.NoSuchProcess:
        return "Not running"
    
def tail(file_path, n=10):
    with open(file_path, "r") as file:
        return list(file)[-n:]
    
def load_config(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    return config

def save_config(config, file_path):
    with open(file_path, 'w') as configfile:
        config.write(configfile)

# Load the .ini file
ini_file_path = 'config.ini'
config = load_config(ini_file_path)

# Display the app title and instructions
st.title("Octonet Node")
st.write("Modify the values in the .ini file using the fields below and click 'Save and Run'.")

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
experiment_id = st.sidebar.text_input("ID", config.get("experiment", "id"))
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
activity_label = st.sidebar.text_input("Activity", value=config.get("label_info", "activity"))
config.set("label_info", "activity", activity_label)

# Display and edit the [device_settings] section
st.subheader("Device Settings")

# Create columns for each device
col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)

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
    depth_cam_min_depth = st.text_input("Minimum Depth Distance (meters)", depth_cam_json.get("min_depth_distance", "0"))
    depth_cam_max_depth = st.text_input("Maximum Depth Distance (meters)", depth_cam_json.get("max_depth_distance", "5"))

    
    depth_cam_json["resolution"] = depth_cam_resolution
    depth_cam_json["depth_format"] = depth_cam_depth_format
    depth_cam_json["color_format"] = depth_cam_color_format
    depth_cam_json["depth_fps"] = depth_cam_depth_fps
    depth_cam_json["color_fps"] = depth_cam_color_fps
    depth_cam_json["Data storage location"] = depth_cam_data_storage_location
    depth_cam_json["Depth_Datatype"] = depth_cam_depth_datatype
    depth_cam_json["RGB_Datatype"] = depth_cam_rgb_datatype
    depth_cam_json["min_depth_distance"] = depth_cam_min_depth
    depth_cam_json["max_depth_distance"] = depth_cam_max_depth
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
    seekthermal_min_temp = st.text_input("min_temp", seekthermal_json["min_temp"])
    seekthermal_max_temp= st.text_input("max_temp", seekthermal_json["max_temp"])

    seekthermal_json["port"] = seekthermal_port
    seekthermal_json["frame_rate"] = seekthermal_frame_rate
    seekthermal_json["color_palette"] = seekthermal_color_palette
    seekthermal_json["shutter_mode"] = seekthermal_shutter_mode
    seekthermal_json["agc_mode"] = seekthermal_agc_mode
    seekthermal_json["temperature_unit"] = seekthermal_temperature_unit
    seekthermal_json["Data storage location"] = seekthermal_data_storage_location
    seekthermal_json["seekthermal_Datatype"] = seekthermal_datatype
    seekthermal_json["min_temp"] = seekthermal_min_temp
    seekthermal_json["max_temp"] = seekthermal_max_temp
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
    # mmwave_setting1 = st.text_input("Setting 1", mmwave_json["setting1"])
    # mmwave_setting2 = st.text_input("Setting 2", mmwave_json["setting2"])
    mmwave_data_storage_location = st.text_input("Data Storage Location", mmwave_json["Data storage location"])
    mmwave_datatype = st.text_input("mmwave_Datatype", mmwave_json["mmwave_Datatype"])

    # mmwave_json["setting1"] = mmwave_setting1
    # mmwave_json["setting2"] = mmwave_setting2
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
    st.markdown("**Polar only can be set on server's page**")
    # polar_json = json.loads(config.get("device_settings", "polar"))
    # polar_record_len = st.text_input("Record Length (in seconds)", polar_json["record_len(in_second)"])
    # polar_data_storage_location = st.text_input("Data Storage Location", polar_json["Data storage location"])
    # polar_datatype = st.text_input("polar_Datatype", polar_json["polar_Datatype"])
    
    
    # polar_json["record_len(in_second)"] = polar_record_len
    # polar_json["Data storage location"] = polar_data_storage_location
    # polar_json["polar_Datatype"] = polar_datatype
    
    
    # config.set("device_settings", "polar", json.dumps(polar_json))

    # if st.button("Start Polar heart rate tracking"):
    #     processes.append(subprocess.Popen(["python","polar/H10/connect_H10.py"], cwd="/home/aiot-mini/code/"))
    #     st.success("Polar process started.")
    
    # # Terminate processes when the "Terminate" button is clicked
    # if st.button("Terminate Polar"):
    #     with open("terminate_polar_flag.txt", "w") as f:
    #         f.write("1")
    #     st.write("Sent termination_polar signal.")
    #     time.sleep(6)  

    #     if os.path.exists("terminate_polar_flag.txt"):
    #         os.remove("terminate_polar_flag.txt")
    #         st.write("Polar modality is ended.")

with col6:
    st.markdown("**Acoustic Recorder Settings**")
    # Play Arguments
    sampling_rate = st.number_input("Sampling Rate", value=config.getint("play_arg", "sampling_rate"))
    amplitude = st.selectbox("Amplitude", options=[0.1, 0.3, 0.5, 1, 2, 2.5], index=[0.1, 0.3, 0.5, 1, 2, 2.5].index(config.getfloat("play_arg", "amplitude")))
    blocksize = st.number_input("Block Size", value=config.getint("play_arg", "blocksize"))
    buffersize = st.number_input("Buffer Size", value=config.getint("play_arg", "buffersize"))
    modulation = st.checkbox("Modulation", value=config.getboolean("play_arg", "modulation"))
    idle = st.number_input("Idle", value=config.getint("play_arg", "idle"))
    wave = st.selectbox("Wave", options=["Kasami", "chirp", "ZC"], index=["Kasami", "chirp", "ZC"].index(config.get("play_arg", "wave")))
    frame_length = st.number_input("Frame Length", value=config.getint("play_arg", "frame_length"))
    nchannels = st.number_input("Channels", value=config.getint("play_arg", "nchannels"))
    nbits = st.number_input("Bits", value=config.getint("play_arg", "nbits"))
    # load_dataplay = st.checkbox("Load Data Play", value=config.getboolean("play_arg", "load_dataplay"))

    # Global Arguments
    delay = st.number_input("Delay", value=config.getint("global_arg", "delay"))
    task = st.text_input("Task", config.get("global_arg", "task"))
    save_root = st.text_input("Save Root", config.get("global_arg", "save_root"))
    # set_save = st.checkbox("Set Save", value=config.getboolean("global_arg", "set_save"))

    # Device Arguments
    input_device = st.selectbox("Input Device", options=["micArray RAW SPK"], index=0) # Modify as needed for actual device options
    output_device = st.selectbox("Output Device", options=["micArray RAW SPK"], index=0) # Modify as needed for actual device options

    config.set("play_arg", "sampling_rate", str(sampling_rate))
    config.set("play_arg", "amplitude", str(amplitude))
    config.set("play_arg", "blocksize", str(blocksize))
    config.set("play_arg", "buffersize", str(buffersize))
    config.set("play_arg", "modulation", str(modulation))
    config.set("play_arg", "idle", str(idle))
    config.set("play_arg", "wave", wave)
    config.set("play_arg", "frame_length", str(frame_length))
    config.set("play_arg", "nchannels", str(nchannels))
    config.set("play_arg", "nbits", str(nbits))
    config.set("global_arg", "delay", str(delay))
    config.set("global_arg", "task", task)
    config.set("global_arg", "save_root", save_root)
    config.set("device_arg", "input_device", input_device)
    config.set("device_arg", "output_device", output_device)

    with open(ini_file_path, 'w') as configfile:
        config.write(configfile)
    
    # Update JSON file
    json_data = {
        "play_arg": {
            "sampling_rate": sampling_rate,
            "amplitude": amplitude,
            "blocksize": blocksize,
            "buffersize": buffersize,
            "modulation": modulation,
            "idle": idle,
            "wave": wave,
            "frame_length": frame_length,
            "nchannels": nchannels,
            "nbits": nbits,
            "load_dataplay": False  # Set default or retrieve from config
        },
        "global_arg": {
            "delay": delay,
            "task": task,
            "save_root": save_root,
            "set_save": True,  # Set default or retrieve from config
            "set_playAndRecord": True
        },
        "device_arg": {
            "input_device": input_device,
            "output_device": output_device
        },
        "process_arg": {
            "num_topK_subcarriers": 50,
            "windows_time": 2
        }
    }

    with open("./acoustic/config_file/config_Kasami.json", 'w') as json_file:
        json.dump(json_data, json_file, indent=4)

with col7:
    st.markdown("**UWB**")
    uwb_json = json.loads(config.get("device_settings", "uwb"))
    uwb_data_storage_location = st.text_input("Data Storage Location", uwb_json["Data storage location"])
    uwb_datatype = st.text_input("uwb_Datatype", uwb_json["uwb_Datatype"])
    uwb_min_dist = st.text_input("min_distance", uwb_json["min_distance"])
    uwb_max_dist= st.text_input("max_distance", uwb_json["max_distance"])

    uwb_json["Data storage location"] = uwb_data_storage_location
    uwb_json["uwb_Datatype"] = uwb_datatype
    uwb_json["min_distance"] = uwb_min_dist
    uwb_json["max_distance"] = uwb_max_dist
    config.set("device_settings", "uwb", json.dumps(uwb_json))

# Add checkboxes for each modality
st.subheader("Select Modalities to Start")
start_ira = st.checkbox("Start IRA")
start_depth_camera = st.checkbox("Start Depth Camera")
start_mmwave = st.checkbox("Start MMWave")
start_seekthermal = st.checkbox("Start Seek Thermal")
start_acoustic_recorder = st.checkbox("Start Acoustic Recorder")
start_acoustic_player = st.checkbox("Start Acoustic Player")
start_uwb = st.checkbox("Start UWB")
start_ToF = st.checkbox("Start ToF")

st.write("Reminder: As a Node, the configs above maybe overwritten by the Center Server. Please refresh this page if you want to edit the configs of this node.")
# print("st.session_state.start_flag222", st.session_state.start_flag)
if st.button("Connect to Polar H10"):
    st.write("Connecting...")
    # Save the global config and log
    save_config(config, ini_file_path)
    config = configparser.ConfigParser()
    config.read(os.path.abspath(os.path.join(os.path.dirname(__file__), 'config.ini')))
    # output_directory = os.path.dirname(os.path.abspath(__file__))
    # current_index = get_next_index_global_log(output_directory)
    # logger = setup_logger_global(output_directory, current_index)
    # config_data = {}
    # for section in config.sections():
    #     config_data[section] = dict(config.items(section))
    # logger.info(f"Loaded Global Configuration: {config_data}")
    process = subprocess.Popen([PYTHON_EXE, "polar/H10/connect_H10.py"], cwd="/home/aiot-mini/code/")
    # wait_for_polar_ready()
    st.session_state.process_dict_polar["Polar"]["pid"] = process.pid
    st.session_state.process_polar.append(process)

    # process_dict["Polar"]["pid"] = process.pid
    # # logger.info(f"Polar starts connecting blue tooth")
    # processes.append(process)
    # print(processes,"processes")
    # print(process_dict,"process_dict")
    # with open("process_dict.json", "w") as f:
    #     json.dump(st.session_state.process_dict, f)

if st.session_state.polar_flag == True:
    print("Polar is ready")
    st.success("Polar is ready! You must use server's Start (Not the 'Save and Run' below)")
    time.sleep(3)  
    st.session_state.polar_flag = False
    st.session_state.polar_ready = True
    

# Save the modified .ini file when the "Save and run" button is clicked
if st.button("Save and Run") or st.session_state.start_flag == True:
    save_config(config, ini_file_path)
    st.success("Config file saved.")
    # if start_polar:
    #     st.write("Waiting for polar's bluetooth connection......")
    # print(processes,"processes")
    # Start recording data
    # st.write("Running and recording data...")
    

    # Save the global config and log
    config = configparser.ConfigParser()
    config.read(os.path.abspath(os.path.join(os.path.dirname(__file__), 'config.ini')))
    output_directory = os.path.dirname(os.path.abspath(__file__))
    current_index = get_next_index_global_log(output_directory)
    print(current_index, "currentindex")
    logger = setup_logger_global(output_directory, current_index)
    config_data = {}
    for section in config.sections():
        config_data[section] = dict(config.items(section))
    logger.info(f"Loaded Global Configuration: {config_data}")

    # Remove for asyn process
    if os.path.exists('polar_ready.txt'):
        os.remove('polar_ready.txt')

    if st.session_state.polar_ready == True:
        logger.info(f"Polar starts recording")
        st.session_state.polar_ready = False

    if start_ira:
        # if start_polar:
        #     wait_for_polar_ready()
        process = subprocess.Popen([PYTHON_EXE, "IRA/IRA.py"], cwd="/home/aiot-mini/code/")
        process_dict["IRA"]["pid"] = process.pid
        logger.info(f"IRA starts recording")
        processes.append(process)

    if start_depth_camera:
        # if start_polar:
        #     wait_for_polar_ready()
        process = subprocess.Popen([PYTHON_EXE, "DeptCam/deptcam.py"], cwd="/home/aiot-mini/code/")
        process_dict["Depth Camera"]["pid"] = process.pid
        logger.info(f"Depth and RGB start recording")
        processes.append(process)

    if start_mmwave:
        # if start_polar:
        #     wait_for_polar_ready()
        process = subprocess.Popen([PYTHON_EXE, "AWR1843-Read-Data-Python-MMWAVE-SDK-3--master/readData_AWR1843.py"], cwd="/home/aiot-mini/code/")
        process_dict["MMWave"]["pid"] = process.pid
        logger.info(f"MMWave starts recording")
        processes.append(process)

    # process = subprocess.Popen(["python", "Audio_Collector/main.py", "json", "/home/aiot-mini/code/Audio_Collector/config_file/speed_playfromfile_new.json"], cwd="/home/aiot-mini/code/")
    # process_dict[process.pid] = "Audio Collector"
    # processes.append(process)

    if start_seekthermal:
        # if start_polar:
        #     wait_for_polar_ready()
        process = subprocess.Popen([PYTHON_EXE, "seekcamera-python/runseek/seekcamera-opencv.py"], cwd="/home/aiot-mini/code/")
        process_dict["SeekThermal"]["pid"] = process.pid
        logger.info(f"Seekthermal starts recording")
        processes.append(process)

    if start_acoustic_recorder:
        # if start_polar:  
        #     wait_for_polar_ready()
        process = subprocess.Popen([PYTHON_EXE, "acoustic/recorder.py", "json", "./acoustic/config_file/config_Kasami.json"], cwd="/home/aiot-mini/code/")
        process_dict["Acoustic Recorder"]["pid"] = process.pid
        logger.info("Acoustic Recorder starts recording")
        processes.append(process)

    if start_acoustic_player:
        # if start_polar:  
        #     wait_for_polar_ready()
        process = subprocess.Popen([PYTHON_EXE, "acoustic/player.py", "json", "./acoustic/config_file/config_Kasami.json"], cwd="/home/aiot-mini/code/")
        process_dict["Acoustic Player"]["pid"] = process.pid
        logger.info("Acoustic Player starts playing")
        processes.append(process)

    
    if start_uwb:
        # if start_polar:
        #         wait_for_polar_ready()
        # time.sleep(0.01) 
        python35_path = '/home/aiot-mini/anaconda3/envs/py35/bin/python3.5'  # Path to Python 3.5 interpreter
        script_path = '/home/aiot-mini/code/uwb/Legacy-SW/ModuleConnector/ModuleConnector-unix-1/python35-x86_64-linux-gnu/pymoduleconnector/examples/XEP_X4M200_X4M300_plot_record_playback_radar_raw_data.py'  # Path to your Python 3.5 script
        script_args = ['-d', '/dev/ttyACM2']  # Arguments for the script

        # Combine the Python interpreter path, script path, and script arguments
        full_command = ["sudo", python35_path, script_path] + script_args
        print(full_command)
        # Call the Python script with arguments
        process_uwb = subprocess.Popen(full_command)
        process_dict["uwb"]["pid"] = process_uwb.pid
        logger.info(f"UWB starts recording")
        processes.append(process_uwb)
    
    if start_ToF:
        process = subprocess.Popen([PYTHON_EXE, "ToF/Tof.py"], cwd="/home/aiot-mini/code/")
        process_dict["ToF"]["pid"] = process.pid
        logger.info(f"ToF starts recording")
        processes.append(process)

    process_dict["Polar"]["pid"] = st.session_state.process_dict_polar["Polar"]["pid"]
    processes.append(st.session_state.process_polar)
    

    with open("process_dict.json", "w") as f:
        json.dump(process_dict, f)

    st.session_state.start_flag = False # Reset the flag after executing the block
     
    # process_dict = {
    # "IRA": {"pid": process.pid, "log_dir": "./IRA/logs/"},
    # "Depth Camera": {"pid": process.pid, "log_dir": "./DeptCam/logs/"},
    # "MMWave": {"pid": process.pid, "log_dir": "./path/to/IRA/log/"},
    # "SeekThermal": {"pid": process.pid, "log_dir": "./seekcamera-python/runseek/logs/"},
    # # "Audio Collector": {"pid": process.pid, "log_dir": "./path/to/IRA/log/"},
    # "Polar": {"pid": process.pid, "log_dir": "./polar/H10/logs/"},
    # }
    # st.subheader("Process Log")
    # time.sleep(6)  # To let the config file to be generated
    # # num_lines = st.slider("Number of log lines to display", 1, 30, 2)

    # for process_name, process_info in process_dict.items():
    #     log_dir = process_info["log_dir"]
    #     log_file_path = find_latest_log_file(log_dir)
    #     if log_file_path:
    #         log_content = tail(log_file_path, n=5)
    #         st.write(f"{process_name} Log:{log_file_path}")
    #         for line in log_content:
    #             st.write(line.strip())
    #     else:
    #         st.write(f"{process_name} Log: No log file found,{log_file_path}")
    # st.subheader("Process Status")
    # for pid, process_name in process_dict.items():
    #     status = get_process_status(pid)
    #     st.write(f"{process_name}: {status}")

    # st.subheader("Process Log")

    # for pid, process_name in process_dict.items():
    #     log_file_path = "path/to/log_file"  
    #     log_content = tail(log_file_path, n=10)
    #     st.write(f"{process_name} Log:")
    #     for line in log_content:
    #         st.write(line.strip())

# Terminate processes when the "Terminate" button is clicked
if st.button("Terminate All") or st.session_state.terminate_flag == True:
    if os.path.exists('polar_ready.txt'):
        os.remove('polar_ready.txt')
    
    with open("terminate_flag.txt", "w") as f:
        f.write("1")
    st.write("Sent termination signal.")
    # Calculate the time this experiment used.
    # Find the latest global log file
    global_log_file_path = find_latest_log_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs"))
    # Restart the log file to insert the termination flag
    output_directory = os.path.dirname(os.path.abspath(__file__))
    current_index = get_next_index_global_log(output_directory)
    log_index = int(current_index) - 1 
    logger_terminate = setup_logger_global_terminate(output_directory, log_index)
    logger_terminate.debug("Logger initialized in Save and Run block")
    logger_terminate.info("Termination flag set")
    if global_log_file_path:
        experiment_duration = get_experiment_duration(global_log_file_path)
        if experiment_duration:
            st.write(f"Experiment duration: {experiment_duration}")
            logger_terminate.info(f"Experiment duration: {experiment_duration}")
        else:
            st.write("Could not calculate experiment duration.")
    else:
        st.write("No global log file found. Please restart the config_editor.py file.")
    
    time.sleep(3)  

    if os.path.exists("terminate_flag.txt"):
        os.remove("terminate_flag.txt")
        st.write("All processes are terminated.")

    # Metric
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    # Function to count the number of pickle files in a directory
    def count_pickle_files(directory):
        pickle_files = glob.glob(os.path.join(directory, '*.pickle'))
        return len(pickle_files)
    
    def count_mp4_files(directory):
        mp4_files = glob.glob(os.path.join(directory, '*.mp4'))
        return len(mp4_files)
    # Reporting where the data and log is stored.
    ira_status_path = os.path.join("IRA", "ira_data_saved_status.txt")
    if os.path.exists(ira_status_path):
        with open(ira_status_path, "r") as f:
            ira_data_saved_status = f.read()

        st.success(ira_data_saved_status)
        logger_terminate.info(f'{ira_data_saved_status}')

        # Assuming the pickle files are stored in the 'data' subdirectory of 'IRA'
        ira_data_directory = os.path.join("IRA", "data")
        number_of_pickles = count_pickle_files(ira_data_directory)

        col1.metric("IRA data", f"{number_of_pickles}", "pickle files saved")
        os.remove(ira_status_path)

    seekthermal_status_path = os.path.join("seekcamera-python","runseek", "seekthermal_data_saved_status.txt")
    if os.path.exists(seekthermal_status_path):
        with open(seekthermal_status_path, "r") as f:
            seekthermal_data_saved_status = f.read()
            st.success(seekthermal_data_saved_status)
            logger_terminate.info(f'{seekthermal_data_saved_status}')

        # Assuming the mp4 files are stored in a specific directory
        # Replace 'your_mp4_directory' with the actual directory where the mp4 files are stored
        seekthermal_mp4_directory = os.path.join("seekcamera-python", "runseek", "data")
        number_of_mp4s = count_mp4_files(seekthermal_mp4_directory)

        col2.metric("SeekThermal data", f"{number_of_mp4s}", "mp4 files saved")
        os.remove(seekthermal_status_path)

    # Function to count the number of directories matching the specific pattern
    def count_matching_directories(base_directory, pattern):
        matching_directories = [name for name in os.listdir(base_directory)
                                if os.path.isdir(os.path.join(base_directory, name))
                                and re.match(pattern, name)]
        return len(matching_directories)

    # Reporting where the DeptCam data is stored
    deptcam_status_path = os.path.join("DeptCam", "deptcam_data_saved_status.txt")
    if os.path.exists(deptcam_status_path):
        with open(deptcam_status_path, "r") as f:
            deptcam_data_saved_status = f.read()

        st.success(deptcam_data_saved_status)
        logger_terminate.info(f'{deptcam_data_saved_status}')

        # Assuming the directories are stored in a specific directory
        deptcam_directory = os.path.join("DeptCam","data")
        directory_pattern = r'\d{14}_node_\d+_modality_depthcam_subject_\d+_activity_\w+_trial_\d+'
        number_of_directories = count_matching_directories(deptcam_directory, directory_pattern)

        col3.metric("Dept and RGB data", f"{number_of_directories}", "RGB and depth directories saved")
        os.remove(deptcam_status_path)

    mmwave_status_path = os.path.join("AWR1843-Read-Data-Python-MMWAVE-SDK-3--master", "mmwave_data_saved_status.txt")
    if os.path.exists(mmwave_status_path):
        with open(mmwave_status_path, "r") as f:
            mmwave_data_saved_status = f.read()
            st.success(mmwave_data_saved_status)
            logger_terminate.info(f'{mmwave_data_saved_status}')

        # Assuming the pickle files are stored in a specific directory
        # Replace 'your_pickle_directory' with the actual directory where the pickle files are stored
        mmwave_pickle_directory = os.path.join("AWR1843-Read-Data-Python-MMWAVE-SDK-3--master", "data")
        number_of_pickles = count_pickle_files(mmwave_pickle_directory)

        col4.metric("MMwave data", f"{number_of_pickles}", "pickle files saved")
        os.remove(mmwave_status_path)

    # Reporting where the Polar data is stored
    polar_status_path = os.path.join("polar", "H10", "polar_data_saved_status.txt")
    if os.path.exists(polar_status_path):
        with open(polar_status_path, "r") as f:
            polar_data_saved_status = f.read()
            st.success(polar_data_saved_status)
            logger_terminate.info(f'{polar_data_saved_status}')

        # Assuming the pickle files are stored in a specific directory
        # Replace 'your_pickle_directory' with the actual directory where the pickle files are stored
        polar_pickle_directory = os.path.join("polar", "H10", "data")
        number_of_pickles = count_pickle_files(polar_pickle_directory)

        col5.metric("Polar data", f"{number_of_pickles}", "pickle files saved")
        os.remove(polar_status_path)

    acoustic_status_path = os.path.join("acoustic", "audio", "acoustic_data_saved_status.txt")
    if os.path.exists(acoustic_status_path):
        with open(acoustic_status_path, "r") as f:
            acoustic_data_saved_status = f.read()
            # Extract current_index using regex
        current_index_match = re.search(r"_([0-9]+)\.wav", acoustic_data_saved_status)
        if current_index_match:
            current_index = int(current_index_match.group(1))
            current_index += 1  # Add one to the current_index
        col6.metric("Acoustic data", f"{current_index}", "1 .wav saved")
        st.success(acoustic_data_saved_status)
        logger_terminate.info(f'{acoustic_data_saved_status}')
        os.remove(acoustic_status_path)

    # acoustic_status_path = os.path.join("acoustic", "audio", "acoustic_data_saved_status.txt")
    # if os.path.exists(acoustic_status_path):
    #     with open(acoustic_status_path, "r") as f:
    #         acoustic_data_saved_status = f.read()
    #         # Extract current_index using regex
    #     current_index_match = re.search(r"_([0-9]+)\.wav", acoustic_data_saved_status)
    #     if current_index_match:
    #         current_index = int(current_index_match.group(1))
    #         current_index += 1  # Add one to the current_index
    #     col6.metric("Acoustic data", f"{current_index}", "1 .wav saved")
    #     st.success(acoustic_data_saved_status)
    #     os.remove(acoustic_status_path)

    uwb_status_path = os.path.join("uwb", "Legacy-SW", "ModuleConnector", "ModuleConnector-unix-1", "python35-x86_64-linux-gnu", "pymoduleconnector", "examples", "uwb_data_saved_status.txt")
    if os.path.exists(uwb_status_path):
        with open(uwb_status_path, "r") as f:
            uwb_data_saved_status = f.read()
            st.success(uwb_data_saved_status)
            logger_terminate.info(f'{uwb_data_saved_status}')

        # Assuming the pickle files are stored in a specific directory
        # Replace 'your_pickle_directory' with the actual directory where the pickle files are stored
        uwb_pickle_directory = os.path.join("uwb", "Legacy-SW", "ModuleConnector", "ModuleConnector-unix-1", "python35-x86_64-linux-gnu", "pymoduleconnector", "examples", "data")
        number_of_pickles = count_pickle_files(uwb_pickle_directory)

        col7.metric("UWB data", f"{number_of_pickles}", ".pickle files saved")
        os.remove(uwb_status_path)

    # Reporting where the ToF data is stored
    ToF_status_path = os.path.join("ToF", "ToF_data_saved_status.txt")
    if os.path.exists(ToF_status_path):
        with open(ToF_status_path, "r") as f:
            ToF_data_saved_status = f.read()
            st.success(ToF_data_saved_status)
            logger_terminate.info(f'{ToF_data_saved_status}')

        # Assuming the pickle files are stored in a specific directory
        # Replace 'your_pickle_directory' with the actual directory where the pickle files are stored
        ToF_pickle_directory = os.path.join("ToF", "data")
        number_of_pickles = count_pickle_files(ToF_pickle_directory)

        col8.metric("ToF data", f"{number_of_pickles}", ".pickle files saved")
        os.remove(ToF_status_path)

    # # Acoustic modality status
    # acoustic_status_path = os.path.join("acoustic", "acoustic_data_saved_status.txt")
    # if os.path.exists(acoustic_status_path):
    #     with open(acoustic_status_path, "r") as f:
    #         acoustic_data_saved_status = f.read()
    #     # Extract current_index using regex
    #     current_index_match = re.search(r"output_(\d+).pickle", acoustic_data_saved_status)
    #     if current_index_match:
    #         current_index = int(current_index_match.group(1))
    #         current_index += 1  # Increment the current index
    #     col6.metric("Acoustic data", f"{current_index}", "1 pickle file saved")
    #     st.success(acoustic_data_saved_status)
    #     os.remove(acoustic_status_path)


    st.session_state.terminate_flag = False
        
# Daemon Process
status_placeholder = st.empty()
while True:
    check_start_flag()
    check_terminate_flag()
    check_polar_ready()
    update_modality_status(status_placeholder)
    time.sleep(1)