# import serial
# import time
# import ast
# import numpy as np
# import cv2
# import os
# from time_utils import get_initial_ntp_and_local_time, get_fake_ntp_timestamp

# def save_timestamp_to_file(fake_ntp_timestamp):
#     directory = 'timestamp'
#     if not os.path.exists(directory):
#         os.makedirs(directory)

#     with open(f"{directory}/fake_ntp_timestamps.txt", "a") as timestamp_file:
#         timestamp_file.write(f"{fake_ntp_timestamp}\n")

# def get_next_index():
#     index = 0
#     while os.path.exists(f'data/ira_output_{index}.txt'):
#         index += 1
#     return index

# # Interpolating the subpage into a complete frame by using the bilinear interpolating method with window size at 3x3.
# def SubpageInterpolating(subpage):
#     shape = subpage.shape
#     mat = subpage.copy()
#     for i in range(shape[0]):
#         for j in range(shape[1]):
#             if mat[i,j] > 0.0:
#                 continue
#             num = 0
#             try:
#                 top = mat[i-1,j]
#                 num = num+1
#             except:
#                 top = 0.0
            
#             try:
#                 down = mat[i+1,j]
#                 num = num+1
#             except:
#                 down = 0.0
            
#             try:
#                 left = mat[i,j-1]
#                 num = num+1
#             except:
#                 left = 0.0
            
#             try:
#                 right = mat[i,j+1]
#                 num = num+1
#             except:
#                 right = 0.0
#             mat[i,j] = (top + down + left + right)/num
#     return mat

# def main():
#     # Open serial port (example with '/dev/tty.SLAB_USBtoUART' replace with your port and desired baud rate)
#     port = '/dev/ttyUSB0'
#     baud_rate = 921600
#     ser = serial.Serial(port, baud_rate, timeout=1)
    
#     Detected_temperature =  np.ones((24,32))*20
#     # Get the initial NTP and local times
#     initial_ntp_time, initial_local_time = get_initial_ntp_and_local_time()
#     if not ser.is_open:
#         print(f"Failed to open serial port {port}")
#         return

#     try:
#         print(f"Reading data from {port} at {baud_rate} baud")
#         old_time = 0
#         index = get_next_index()
#         with open(f'data/ira_output_{index}.txt', 'w') as output_file:
#             while True:
#                 data = ser.readline().strip()
#                 if len(data) > 0:
#                     msg_str = str(data.decode('utf-8'))
#                 # time.sleep(0.1)
#                 try:
#                     dict_data = ast.literal_eval(msg_str)
#                     # esp32_timestamp = dict_data["Timestamp"]
#                     Onboard_timestamp = int(dict_data["loc_ts"])
#                     Ambient_temperature = float(dict_data["AT"])
#                     Detected_temperature = np.array(dict_data["data"]).reshape((24,32))
#                     current_date, current_time = get_time()
#                     print(f"Timestamp: {Onboard_timestamp} | Ambient Temperature: {Ambient_temperature} | Detected Temperature: {Detected_temperature}")
#                     output_str = f"Timestamp: {Onboard_timestamp} | Ambient Temperature: {Ambient_temperature} | Detected Temperature:{Detected_temperature}"
                    
#                     output_file.write(output_str + "\n")
#                     # Get the adjusted timestamp
#                     # fake_ntp_timestamp = get_fake_ntp_timestamp(initial_ntp_time, initial_local_time)
#                     # print("Server's timestamp:", fake_ntp_timestamp)
#                     # Save the temperature data and timestamp
#                     save_temperature_data(fake_ntp_timestamp)
#                     # new_time = Onboard_timestamp
#                     # diff_time = new_time - old_time
#                     # old_time = Onboard_timestamp
#                     # print("time difference", diff_time)
#                 except:
#                     print("Error")
                
#                     print(Detected_temperature.shape)
#                 ira_interpolated = SubpageInterpolating(Detected_temperature)
#                 ira_norm = ((ira_interpolated - np.min(ira_interpolated))/ (37 - np.min(ira_interpolated))) * 255
#                 ira_expand = np.repeat(ira_norm, 20, 0)
#                 ira_expand = np.repeat(ira_expand, 20, 1)
#                 ira_img_colored = cv2.applyColorMap((ira_expand).astype(np.uint8), cv2.COLORMAP_JET)
#                 cv2.namedWindow('All', cv2.WINDOW_AUTOSIZE)
#                 cv2.imshow('All', ira_img_colored)
#                 key = cv2.waitKey(1) 
#                 if key == 27 or key == 113:
#                     break
            
#         # cv2.destroyAllWindows()   
#     except KeyboardInterrupt:
#         print("Exiting...")
#     finally:
#         ser.close()

# if __name__ == "__main__":
#     main()

# import os
# import serial
# import time
# import ast
# import numpy as np
# import cv2
# from time_utils import *

# def get_next_index():
#     index = 0
#     while True:
#         if not (os.path.exists(f"data/ira_output_{index}.txt") and os.path.exists(f"timestamp/ira_timestamp_{index}.txt")):
#             break
#         index += 1
#     return index
# # Interpolating the subpage into a complete frame by using the bilinear interpolating method with window size at 3x3.
# def SubpageInterpolating(subpage):
#     shape = subpage.shape
#     mat = subpage.copy()
#     for i in range(shape[0]):
#         for j in range(shape[1]):
#             if mat[i,j] > 0.0:
#                 continue
#             num = 0
#             try:
#                 top = mat[i-1,j]
#                 num = num+1
#             except:
#                 top = 0.0
            
#             try:
#                 down = mat[i+1,j]
#                 num = num+1
#             except:
#                 down = 0.0
            
#             try:
#                 left = mat[i,j-1]
#                 num = num+1
#             except:
#                 left = 0.0
            
#             try:
#                 right = mat[i,j+1]
#                 num = num+1
#             except:
#                 right = 0.0
#             mat[i,j] = (top + down + left + right)/num
#     return mat

# def main():
#     # Open serial port (example with '/dev/tty.SLAB_USBtoUART' replace with your port and desired baud rate)
#     port = '/dev/ttyUSB0'
#     baud_rate = 921600
#     ser = serial.Serial(port, baud_rate, timeout=1)
    
#     Detected_temperature =  np.ones((24,32))*20

#     if not ser.is_open:
#         print(f"Failed to open serial port {port}")
#         return

#     # Create directories for output files if they don't already exist
#     if not os.path.exists("data"):
#         os.makedirs("data")

#     if not os.path.exists("timestamp"):
#         os.makedirs("timestamp")

#     # Get the initial NTP and local time
#     initial_ntp_time, initial_local_time = get_initial_ntp_and_local_time()

#     index = get_next_index()

#     try:
#         print(f"Reading data from {port} at {baud_rate} baud")
#         with open(f"data/ira_output_{index}.txt", "w") as data_file, open(f"timestamp/ira_timestamp_{index}.txt", "w") as timestamp_file:
#             while True:
#                 data = ser.readline().strip()
#                 if len(data) > 0:
#                     msg_str = str(data.decode('utf-8'))
#                 # time.sleep(0.1)
#                 try:
#                     dict_data = ast.literal_eval(msg_str)
#                     # esp32_timestamp = dict_data["Timestamp"]
#                     Onboard_timestamp = int(dict_data["loc_ts"])
#                     Ambient_temperature = float(dict_data["AT"])
#                     Detected_temperature = np.array(dict_data["data"]).reshape((24,32))
#                     # Save the output to the respective files
#                     data_file.write(f"Timestamp: {Onboard_timestamp} | Ambient Temperature: {Ambient_temperature} | Detected Temperature: {Detected_temperature}\n")

#                     fake_ntp_timestamp = time_utils.get_fake_ntp_timestamp(initial_ntp_time, initial_local_time)
#                     timestamp_file.write(fake_ntp_timestamp + "\n")

                    
#                     print(f"Timestamp: {Onboard_timestamp} | Ambient Temperature: {Ambient_temperature} | Detected Temperature: {Detected_temperature}")
#                     # new_time = Onboard_timestamp
#                     # diff_time = new_time - old_time
#                     # old_time = Onboard_timestamp
#                     # print("time difference", diff_time)
#                 except:
#                     print("Error")
                
#                     print(Detected_temperature.shape)
#                 ira_interpolated = SubpageInterpolating(Detected_temperature)
#                 ira_norm = ((ira_interpolated - np.min(ira_interpolated))/ (37 - np.min(ira_interpolated))) * 255
#                 ira_expand = np.repeat(ira_norm, 20, 0)
#                 ira_expand = np.repeat(ira_expand, 20, 1)
#                 ira_img_colored = cv2.applyColorMap((ira_expand).astype(np.uint8), cv2.COLORMAP_JET)
#                 cv2.namedWindow('All', cv2.WINDOW_AUTOSIZE)
#                 cv2.imshow('All', ira_img_colored)
#                 key = cv2.waitKey(1) 
#                 if key == 27 or key == 113:
#                     break
            
#         # cv2.destroyAllWindows()   
#     except KeyboardInterrupt:
#         print("Exiting...")
#     finally:
#         ser.close()

# if __name__ == "__main__":
#     main()





import serial
import time
import ast
import numpy as np
import cv2
import os
import ntplib
from datetime import datetime
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from time_utils import *
from save_timestamp_data import *
from log_utils import *
from sampling_rate import SamplingRateCalculator
import configparser
import json
import math

# To see the size of the saved pickle
def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

# For receiving the termination signal from the streamlit
def check_terminate_flag():
    if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '../terminate_flag.txt')))or os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '../terminate_ira_flag.txt'))):
        # os.remove("terminate_flag.txt")
        return True
    return False
# def save_ira_data(data, timestamp, subindex, output_directory):
#     data_folder = os.path.join(output_directory, "data")
#     # timestamp_folder = os.path.join(output_directory, "timestamp")

#     if not os.path.exists(data_folder):
#         os.makedirs(data_folder)

#     # if not os.path.exists(timestamp_folder):
#     #     os.makedirs(timestamp_folder)

#     with open(os.path.join(data_folder, f'output_{subindex}.txt'), 'a') as f:
#         f.write(f"{data}\n")

    # with open(os.path.join(timestamp_folder, f'timestamp_{subindex}.txt'), 'a') as f:
    #     f.write(f"Timestamp: {timestamp}\n")
# Interpolating the subpage into a complete frame by using the bilinear interpolating method with window size at 3x3.
def SubpageInterpolating(subpage):
    shape = subpage.shape
    mat = subpage.copy()
    for i in range(shape[0]):
        for j in range(shape[1]):
            if mat[i,j] > 0.0:
                continue
            num = 0
            try:
                top = mat[i-1,j]
                num = num+1
            except:
                top = 0.0
            
            try:
                down = mat[i+1,j]
                num = num+1
            except:
                down = 0.0
            
            try:
                left = mat[i,j-1]
                num = num+1
            except:
                left = 0.0
            
            try:
                right = mat[i,j+1]
                num = num+1
            except:
                right = 0.0
            mat[i,j] = (top + down + left + right)/num
    return mat

def main():
    # Calculate the actual sampling rate
    sampler = SamplingRateCalculator("IRA")
    # Initialize the frame to calculate the total frame
    frame_counter = 0
    # Initial config.ini
    config = configparser.ConfigParser()
    config.read(os.path.abspath(os.path.join(os.path.dirname(__file__), '../config.ini')))
    ira_settings_str = config.get('device_settings', 'ira')
    ira_settings = json.loads(ira_settings_str)
    # Open serial port (example with '/dev/tty.SLAB_USBtoUART' replace with your port and desired baud rate)
    port = ira_settings['port']
    baud_rate = int(ira_settings['baud_rate'])
    ser = serial.Serial(port, baud_rate, timeout=1)
    Detected_temperature =  np.ones((24,32))*20
    #General setting
    output_directory = os.path.dirname(os.path.abspath(__file__))
    current_index = get_next_index(output_directory)
    # Log 
    logger = setup_logger(output_directory, current_index)
    config_data = {}
    for section in config.sections():
        if section != 'device_settings':
            config_data[section] = dict(config.items(section))
    logger.info(f"Loaded configuration: {config_data}")
    logger.info(f"Loaded IRA configuration: {ira_settings}")
    # subindex = 0
    # data_filename = os.path.join(output_directory, "data", f'output_{subindex}.pickle')
    # while os.path.exists(data_filename):
    #     subindex += 1
    #     data_filename = os.path.join(output_directory, "data", f'output_{subindex}.pickle')
    if not ser.is_open:
        print(f"Failed to open serial port {port}")
        return

    try:
        logger.info(f"Reading data from {port} at {baud_rate} baud")
        old_time = 0
        timeflag = True
        data_folder = os.path.join(output_directory, "data")

        if not os.path.exists(data_folder):
            os.makedirs(data_folder)

        file_path = os.path.join(data_folder, f'output_{current_index}.pickle')
        with open(file_path, 'ab') as f:
            while True:
                # print("data_filename", data_filename)
                data = ser.readline().strip()
                if len(data) > 0:
                    msg_str = str(data.decode('utf-8'))
                # time.sleep(0.1)
                try:
                    dict_data = ast.literal_eval(msg_str)
                    # esp32_timestamp = dict_data["Timestamp"]
                    Onboard_timestamp = int(dict_data["loc_ts"])
                    Ambient_temperature = float(dict_data["AT"])
                    Detected_temperature = np.array(dict_data["data"]).reshape((24,32))
                    
                    # new_time = Onboard_timestamp
                    # diff_time = new_time - old_time
                    # old_time = Onboard_timestamp
                    # print("time difference", diff_time)
                    if timeflag:
                        ntp_time, time_difference = get_ntp_time_and_difference()
                        fake_ntp_timestamp = ntp_time
                        logger.info("Using NTP time as the start timmer.")
                        timeflag = False
                    else:
                        current_local_time = datetime.now()
                        fake_ntp_timestamp = get_fake_ntp_time(current_local_time, time_difference)
                        logger.info("Using the local timmer to pretend to be NTP time. Data recorded")
                    print("current_local_time:", current_local_time)
                    print(f"NTP_Server_timestamp:, {fake_ntp_timestamp}")
                    # Save frame data and timestamp
                    
                    output_str = f"Ambient Temperature: {Ambient_temperature} | Detected Temperature:{Detected_temperature}"
                    save_timestamp_data_modified(output_str, fake_ntp_timestamp, f)
                except:
                    logger.error("Error")
                
                    print(Detected_temperature.shape)
                ira_interpolated = SubpageInterpolating(Detected_temperature)
                ira_norm = ((ira_interpolated - np.min(ira_interpolated))/ (37 - np.min(ira_interpolated))) * 255
                ira_expand = np.repeat(ira_norm, 20, 0)
                ira_expand = np.repeat(ira_expand, 20, 1)
                ira_img_colored = cv2.applyColorMap((ira_expand).astype(np.uint8), cv2.COLORMAP_JET)
                cv2.namedWindow('All', cv2.WINDOW_AUTOSIZE)
                cv2.imshow('All', ira_img_colored)
                key = cv2.waitKey(1) 
                # To calculate the actual sampling rate
                sampler.update_loop()
                # Calculate the total frame
                frame_counter += 1
                if key == 27 or key == 113 or check_terminate_flag():
                    logger.info("End recording by a terminate action.")
                    pickle_size = os.path.getsize(file_path)
                    human_readable_size = convert_size(pickle_size)
                    with open(os.path.join(os.path.dirname(__file__), "ira_data_saved_status.txt"), "w") as f:
                        f.write(f"IRA Data saved /IRA/data/output_{current_index}.pickle,\n")
                        f.write(f"IRA Log saved /IRA/logs/config_{current_index}.log,\n")
                        f.write(f"Total frames processed: {frame_counter},\n")
                        f.write(f"Pickle file size: {human_readable_size}\n")
                    break
            
        # cv2.destroyAllWindows()   
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        ser.close()

if __name__ == "__main__":
    main()


