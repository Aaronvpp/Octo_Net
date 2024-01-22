from threading import Condition
import math 
import cv2
import os
import glob
import ntplib
from time import ctime
from datetime import datetime
import pickle
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from time_utils import *
from save_timestamp_data import *
from log_utils import *
from sampling_rate import SamplingRateCalculator
import configparser
import json
import math
import numpy as np

from seekcamera import (
    SeekCameraIOType,
    SeekCameraColorPalette,
    SeekCameraManager,
    SeekCameraManagerEvent,
    SeekCameraFrameFormat,
    SeekCamera,
    SeekFrame, SeekCameraShutterMode, SeekCameraAGCMode, SeekCameraTemperatureUnit
)


# To see the size of the saved pickle
def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

# def save_temperature_data(temp_data, index, timestamp, output_directory):
#     data_folder = os.path.join(output_directory, "data")
    
#     if not os.path.exists(data_folder):
#         os.makedirs(data_folder)

#     file_path = os.path.join(data_folder, f'seekoutput_{index}.pickle')
    
#     # Load existing data if the file exists
#     if os.path.exists(file_path):
#         with open(file_path, 'rb') as f:
#             existing_data = pickle.load(f)
#     else:
#         existing_data = []

#     data_dict = {"timestamp": timestamp, "temperature_data": temp_data}
#     existing_data.append(data_dict)
    
#     with open(file_path, 'wb') as f:
#         pickle.dump(existing_data, f)


# def get_next_index(output_directory):
#     data_folder = os.path.join(output_directory, "data")
#     existing_files = glob.glob(os.path.join(data_folder, 'seekoutput_*.pickle'))
#     indices = [int(os.path.splitext(os.path.basename(f))[0].split('_')[1]) for f in existing_files]
#     return max(indices) + 1 if indices else 0

class Renderer:
    def __init__(self):
        self.busy = False
        self.frame = SeekFrame()
        self.camera = SeekCamera()
        self.frame_condition = Condition()
        self.first_frame = True


def on_frame(_camera, camera_frame, renderer):
    print("on_frame called")
    with renderer.frame_condition:
        renderer.frame1 = camera_frame.thermography_float
        renderer.frame = camera_frame.color_argb8888
        renderer.frame_condition.notify()

# For receiving the termination signal from the streamlit
def check_terminate_flag():
    if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../terminate_flag.txt'))) or os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../terminate_seek_flag.txt'))):
        # os.remove("terminate_flag.txt")
        return True
    return False

def on_event(camera, event_type, event_status, renderer):
    print("{}: {}".format(str(event_type), camera.chipid))

    if event_type == SeekCameraManagerEvent.CONNECT:
        if renderer.busy:
            return
        renderer.busy = True
        renderer.camera = camera
        renderer.first_frame = True
        camera.color_palette = SeekCameraColorPalette.TYRIAN
        camera.shutter_mode = SeekCameraShutterMode.MANUAL
        camera.agMode =  SeekCameraAGCMode.LINEAR
        camera.tempunit = SeekCameraTemperatureUnit.CELSIUS
        camera.register_frame_available_callback(on_frame, renderer)
        camera.capture_session_start(SeekCameraFrameFormat.THERMOGRAPHY_FLOAT | SeekCameraFrameFormat.COLOR_ARGB8888)
        # camera.capture_session_start(SeekCameraFrameFormat.COLOR_ARGB8888)

    elif event_type == SeekCameraManagerEvent.DISCONNECT:
        if renderer.camera == camera:
            # Stop imaging and reset all the renderer state.
            camera.capture_session_stop()
            renderer.camera = None
            renderer.frame = None
            renderer.busy = False
    elif event_type == SeekCameraManagerEvent.ERROR:
        print("{}: {}".format(str(event_status), camera.chipid))
    elif event_type == SeekCameraManagerEvent.READY_TO_PAIR:
        return

def on_click(event, x, y, p1, temp_params):
    temp,img = temp_params
    if event == cv2.EVENT_LBUTTONDOWN:
        print("Pixel Temperature is: ", temp[y, x]," °C. At coordinate: ",x, y)
        cv2.circle(img, (x, y), 3, (0, 0, 0), -1)
        # cv2.imshow("Seek Thermal - Python OpenCV Sample", img)

def main():   
    # Create lists to store timestamps
    seekthermal_video_timestamps = []
    #for testing the MSE
    # Initialize a list to store the frames
    all_depth_frames = []
    # Calculate the actual sampling rate
    sampler = SamplingRateCalculator("SeekThermal")
    # Initialize the frame to calculate the total frame
    frame_counter = 0
    # Initial config.ini
    config = configparser.ConfigParser()
    config.read(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../config.ini')))
    seekthermal_settings_str = config.get('device_settings', 'seekthermal')
    seekthermal_settings = json.loads(seekthermal_settings_str)
    min_temp = float(seekthermal_settings.get('min_temp')) 
    max_temp = float(seekthermal_settings.get('max_temp'))
    output_directory = os.path.dirname(os.path.abspath(__file__))
    # pickle_idx = 0
    experiment_idx = get_next_index_seekthermal(output_directory)
    # current_index = get_next_index(output_directory)
    window_name = "Seek Thermal - Python OpenCV Sample"
    # cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    timeflag = True
    logger = setup_logger(output_directory, experiment_idx)
    config_data = {}
    for section in config.sections():
        if section != 'device_settings':
            config_data[section] = dict(config.items(section))
    logger.info(f"Loaded configuration: {config_data}")
    logger.info(f"Loaded Seek Thermal configuration: {seekthermal_settings}")
    # seekthermal_settings_str = config.get('device_settings', 'seekthermal')
    # seekthermal_settings = json.loads(seekthermal_settings_str)
    frame_rate = float(seekthermal_settings.get('frame_rate'))
    timeout = 1/frame_rate
    data_folder = os.path.join(output_directory, "data")

    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    file_path = os.path.join(data_folder, f'output_{experiment_idx}.pickle')
    thermal_video_filename = os.path.join(data_folder, f'thermal_{experiment_idx}.mp4')
    
    # Open the file in append mode ('ab')
    #with open(file_path, 'ab') as f:
    
    with SeekCameraManager(SeekCameraIOType.USB) as manager:
        renderer = Renderer()
        manager.register_event_callback(on_event, renderer)

        
        while True:
            with renderer.frame_condition:
                if renderer.frame_condition.wait(timeout):
                    img = renderer.frame.data
                    temp = renderer.frame1.data

                    if renderer.first_frame:
                        (height, width,_ ) = img.shape
                        # cv2.resizeWindow(window_name, width * 2, height * 2)
                        renderer.first_frame = False
                        thermal_video_writer = cv2.VideoWriter(thermal_video_filename, cv2.VideoWriter_fourcc(*'mp4v'), frame_rate, (width, height))
                        
                    # cv2.setMouseCallback(window_name, on_click,(temp,img))
                    # cv2.imshow(window_name, img)
                    print("Temperature data:", temp)
                    print(temp.dtype)
                    # Filter out temperature values outside the range [min_temp, max_temp]
                    temp_filtered = np.clip(temp, min_temp, max_temp)
                    # Append the filtered frame to the list(for testing purposes)
                    # all_depth_frames.append(temp_filtered)
                    # Normalize to the range [0, 255]
                    temp_normalized = cv2.normalize(temp_filtered, None, 0, 255, cv2.NORM_MINMAX)
                    temp_normalized = np.uint8(temp_normalized)
                    # Inside the while True loop, after processing the temperature data
                    color_mapped_temp = cv2.applyColorMap(temp_normalized, cv2.COLORMAP_JET)
                    thermal_video_writer.write(color_mapped_temp)
                    
                    # Get the current local time
                    # timestamp = get_local_time()
                    # # Get the current NTP time
                    # #timestamp = get_ntp_time()
                    # print("NTP timestamp:" ,timestamp)
                    # Get the adjusted timestamp
                    if timeflag:
                        ntp_time, time_difference = get_ntp_time_and_difference()
                        fake_ntp_timestamp = ntp_time
                        logger.info("Using NTP time as the start timmer.")
                        timeflag = False
                    else:
                        current_local_time = datetime.now()
                        fake_ntp_timestamp = get_fake_ntp_time(current_local_time, time_difference)
                        logger.info("Using the local timmer to pretend to be NTP time. Data recorded")
                    
                    # Save frame data and timestamp
                    print("fake_ntp_timestamp", fake_ntp_timestamp)
                    # Append the timestamp to the list
                    seekthermal_video_timestamps.append(fake_ntp_timestamp)
                    # Save the temperature data and timestamp
                    #save_timestamp_data_modified(temp, fake_ntp_timestamp, f)
                    # pickle_idx = pickle_idx + 1
                    # To calculate the actual sampling rate
                    sampler.update_loop()
                    # Calculate the total frame
                    frame_counter += 1
            

            key = cv2.waitKey(1)
            if key == ord("q") or check_terminate_flag():
                # After the loop, save all frames in one .npy file(for testing purposes)
                # npy_filepath = os.path.join(data_folder, f'all_depth_frames_{experiment_idx}.npy')
                # np.save(npy_filepath, np.array(all_depth_frames))
                # save all frames in one .npy file(for testing purposes)
                thermal_video_writer.release()
                # Measure the size of the MP4 file
                mp4_size = os.path.getsize(thermal_video_filename)
                human_readable_mp4_size = convert_size(mp4_size)
                logger.info("End recording by a terminate action.")
                with open(os.path.join(data_folder, f'timestamps_{experiment_idx}.txt'), 'w') as f:
                    for timestamp in seekthermal_video_timestamps:
                        f.write(f"{timestamp}\n")
                #pickle_size = os.path.getsize(file_path)
                #human_readable_size = convert_size(pickle_size)
                with open(os.path.join(os.path.dirname(__file__), "seekthermal_data_saved_status.txt"), "w") as f:
                    #f.write(f"seekthermal Data saved seekcamera-python/runseek/data/output_{experiment_idx}.pickle,\n")
                    f.write(f"seekthermal Data saved /seekThermal/data/thermal_{experiment_idx}.mp4\n")
                    f.write(f"seekthermal Log saved /seekThermal/logs/config_{experiment_idx}.log\n")
                    f.write(f"Total frames processed: {frame_counter},\n")
                    f.write(f"Thermal video file size: {human_readable_mp4_size}\n")
                    #f.write(f"Pickle file size: {human_readable_size}\n")
                break

            # if not cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE):
            #     break
        
            

    # cv2.destroyWindow(window_name)


if __name__ == "__main__":
    main()