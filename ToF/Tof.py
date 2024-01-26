import serial
import time
import ast
import numpy as np
import cv2
# import mediapipe as mp
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
# import cv2
import struct
import os
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import pyrealsense2 as rs
import pickle
import argparse
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

def main(save_flag, visualize_flag, tof_port='/dev/ttyACM2'):
    # save_flag = False
    visualize_flag = True
    log_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())

    # Open ToF seral port
    baud_rate = 921600
    tof_ser = serial.Serial(tof_port, baud_rate, timeout=1)
    if not tof_ser.is_open:
        print(f"Failed to open tof serial port {tof_port}")
        return
    end = b"ND\n"


    
    if save_flag:
        save_folder = "tmp/"+ "/"+log_time+"/"
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)


    ira_data = None
    tof_bins = None
    tof_depth = None
    color_image = None
    depth_image = None

    # save_tof_depth = []
    # save_ira_data = []
    # save_tof_bins = []

    # save_pickle = {"ira_data":[], "tof_bins": [], "tof_depth": [], "rgb_path": [], "depth_path": []}
    cv2.namedWindow('All', cv2.WINDOW_AUTOSIZE)
    timeflag = True
    # Calculate the actual sampling rate
    sampler = SamplingRateCalculator("ToF")
    # Initialize the frame to calculate the total frame
    frame_counter = 0
    # Initial config.ini
    config = configparser.ConfigParser()
    config.read(os.path.abspath(os.path.join(os.path.dirname(__file__), '../config.ini')))
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
    # logger.info(f"Loaded IRA configuration: {ira_settings}")
    data_folder = os.path.join(output_directory, "data")
    visualize_flag = True
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    file_path = os.path.join(data_folder, f'output_{current_index}.pickle')
    with open(file_path, 'ab') as f:
        while True:
            
            try:
                # tof_bins = None
                # tof_depth = None
                data = tof_ser.read_until(end)
                int16s = []
                bins = []
                for i in range(4, len(data)-4, 92):
                    int16 = struct.unpack('>H', data[i:i+2])[0]
                    int16s.append(int16)
                    for j in range(2, 92, 5):
                        ind = i + j
                        int32 = struct.unpack('>I', data[ind:ind+4])[0]
                        int8 = data[ind+4]
                        binv = int32/(2<<int8)
                        bins.append(binv)
                tof_bins = np.array(bins).reshape((8,8, 18))
                tof_bins = np.flip(tof_bins,0)
                tof_bins = np.flip(tof_bins,1)
                tof_bins = tof_bins.reshape((64,18))
                tof_depth = np.array(int16s).reshape(8, 8)
                tof_depth = np.flip(tof_depth,0)
                tof_depth = np.flip(tof_depth,1)
                # save_timestamp_data_modified(output_str, fake_ntp_timestamp, f)
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
                data_dict = {"timestamp": fake_ntp_timestamp, "tof_bins": tof_bins, "tof_depth": tof_depth}
                pickle.dump(data_dict, f)
                # To calculate the actual sampling rate
                sampler.update_loop()
                # Calculate the total frame
                frame_counter += 1
            except:

                pass

            
            # align the data
            # color_image = color_image[220:620, 20:420, :]
            # depth_image = depth_image[220:620, 20:420]
            # if save_flag == 1:
            #     if ira_data is not None and tof_depth is not None and color_image is not None and depth_image is not None:
            #         save_tof_depth.append(tof_depth)
            #         save_tof_bins.append(tof_bins)


            if visualize_flag:
                if tof_depth is not None:
                    vis_data = cv2.resize(tof_depth, (400, 400), interpolation=cv2.INTER_NEAREST)
                    vis_data = (vis_data) / (3500)*255
                    vis_data[vis_data > 255] = 255
                    vis_data = cv2.applyColorMap((vis_data).astype(np.uint8), cv2.COLORMAP_JET)
                    # vis_data = np.flip(vis_data, 0)

                    
                    bin_data = (tof_bins) / tof_bins.max()*255
                    bin_data[bin_data > 255] = 255
                    bin_data = cv2.applyColorMap((bin_data).astype(np.uint8), cv2.COLORMAP_JET)
                    bin_data = cv2.resize(bin_data, (400, 400), interpolation=cv2.INTER_NEAREST)
                    # bin_data = np.flip(bin_data, 0)
                    
                    show_data = cv2.hconcat([vis_data,bin_data])
                    cv2.imshow('All', show_data)
                else:
                    print("Error")
                if cv2.waitKey(1) & 0xFF == ord('q') or check_terminate_flag():
                    logger.info("End recording by a terminate action.")
                    pickle_size = os.path.getsize(file_path)
                    human_readable_size = convert_size(pickle_size)
                    with open(os.path.join(os.path.dirname(__file__), "ToF_data_saved_status.txt"), "w") as f:
                        f.write(f"ToF Data saved /ToF/data/output_{current_index}.pickle,\n")
                        f.write(f"ToF Log saved /ToF/logs/config_{current_index}.log,\n")
                        f.write(f"Total frames processed: {frame_counter},\n")
                        f.write(f"Pickle file size: {human_readable_size}\n")
                    break
        if visualize_flag:
            cv2.destroyAllWindows()
        tof_ser.close()
              


    # if save_flag == 1:
    #     save_tof_bins = np.array(save_tof_bins)
    #     save_tof_depth = np.array(save_tof_depth)
    #     save_ira_data = np.array(save_ira_data)
    #     save_pickle["tof_bins"] = save_tof_bins
    #     save_pickle["tof_depth"] = save_tof_depth
        
    #     # save the pickle file
    #     with open(save_folder + "/data.pkl", 'wb') as f:
    #         pickle.dump(save_pickle, f)


if __name__ == "__main__":
    #python Tof.py --save_flag 1 --visualize_flag 1
    parser = argparse.ArgumentParser()
    parser.add_argument('--save_flag', type=int, default=0, help='save data or not')
    parser.add_argument('--visualize_flag', type=int, default=1, help='visualize data or not')
    args = parser.parse_args()
    save_flag = args.save_flag
    visualize_flag = args.visualize_flag

    # user_id = "P1_1_1"
    # save_flag = 1
    # visualize_flag = 1

    main(save_flag, visualize_flag)