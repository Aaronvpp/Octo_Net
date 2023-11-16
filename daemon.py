import time
import os
import psutil
import json

def get_process_status(pid):
    try:
        process = psutil.Process(pid)
        return process.status()
    except psutil.NoSuchProcess:
        return "Not running"

def read_process_dict(file_path):
    with open(file_path, "r") as f:
        process_dict = json.load(f)
    return process_dict

# Initialize process_dict with empty PIDs
process_dict = {
    "IRA": {"pid": None},
    "Depth Camera": {"pid": None},
    "MMWave": {"pid": None},
    "SeekThermal": {"pid": None},
    "Polar": {"pid": None},
}

process_dict_file = "process_dict.json"

while True:
    # Check if the process_dict.json file exists
    if os.path.exists(process_dict_file):
        # Read the updated process_dict from the file
        process_dict = read_process_dict(process_dict_file)

    status_dict = {}
    for process_name, process_info in process_dict.items():
        if process_info["pid"] is not None:
            status = get_process_status(process_info["pid"])
            status_dict[process_name] = {"status": status, "sampling_rate": 0.0}

    with open("status.json", "w") as f:
        json.dump(status_dict, f)

    time.sleep(3)