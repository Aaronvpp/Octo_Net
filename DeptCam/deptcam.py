import pyrealsense2 as rs
import numpy as np
import cv2
import os
import pickle
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from time_utils import *
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
    if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '../terminate_flag.txt'))) or os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '../terminate_depthcam_flag.txt'))):
        # os.remove("terminate_flag.txt")
        return True
    return False

# Calculate the actual sampling rate
sampler = SamplingRateCalculator("Depth Camera")
# Initialize the frame to calculate the total frame
frame_counter = 0
# Create output directories
output_directory = os.path.dirname(os.path.abspath(__file__))
index = 0
config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join(os.path.dirname(__file__), '../config.ini')))

depth_settings_str = config.get('device_settings', 'depth_cam')
depth_settings = json.loads(depth_settings_str)
while True:
    main_output_folder = f'output_{index}'
    main_output_path = os.path.join(output_directory, main_output_folder)
    depth_output_folder = f'depth_image_output_{index}'
    depth_output_path = os.path.join(main_output_path, depth_output_folder)
    rgb_output_folder = f'rgb_video_output_{index}'
    rgb_output_path = os.path.join(main_output_path, rgb_output_folder)
    if not os.path.exists(main_output_path):
        os.makedirs(main_output_path)
        os.makedirs(depth_output_path)
        os.makedirs(rgb_output_path)
        break
    index += 1

logger = setup_logger(output_directory, index)
config_data = {}
for section in config.sections():
    if section != 'device_settings':
        config_data[section] = dict(config.items(section))
logger.info(f"Loaded configuration: {config_data}")
logger.info(f"Loaded DepthCam configuration: {depth_settings}")
depth_cam_settings_str = config.get('device_settings', 'depth_cam')
depth_cam_settings = json.loads(depth_cam_settings_str)
# Get the resolution values
resolution = depth_cam_settings.get('resolution', "640x480").split("x")
width = int(resolution[0])
height = int(resolution[1])

# Get the depth and color formats
depth_format = getattr(rs.format, depth_cam_settings.get('depth_format', "z16"))
color_format = getattr(rs.format, depth_cam_settings.get('color_format', "bgr8"))

# Get the frame rates
depth_fps = int(depth_cam_settings.get('depth_fps', 30))
color_fps = int(depth_cam_settings.get('color_fps', 30))


# Define the codec and create VideoWriter objects
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
rgb_video_filename = os.path.join(rgb_output_path, 'rgb_video.mp4')
rgb_video_writer = cv2.VideoWriter(rgb_video_filename, fourcc, color_fps, (width, height))

# Configure depth and color streams
pipeline = rs.pipeline()
config = rs.config()

# Get device product line for setting a supporting resolution
pipeline_wrapper = rs.pipeline_wrapper(pipeline)
pipeline_profile = config.resolve(pipeline_wrapper)
device = pipeline_profile.get_device()
depth_sensor = pipeline_profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()
# print("depth_scale: ", depth_scale)

device_product_line = str(device.get_info(rs.camera_info.product_line))

found_rgb = False
for s in device.sensors:
    if s.get_info(rs.camera_info.name) == 'RGB Camera':
        found_rgb = True
        break
if not found_rgb:
    print("The demo requires Depth camera with Color sensor")
    exit(0)

# config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.depth, width, height, depth_format, depth_fps)
if device_product_line == 'L500':
    config.enable_stream(rs.stream.color, 960, 540, rs.format.bgr8, 30)
else:
    # config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.color, width, height, color_format, color_fps)
# Start streaming
pipeline.start(config)

frame_number = 0
# Create lists to store timestamps
rgb_video_timestamps = []
depth_image_timestamps = []
timeflag = True
try:
 
    file_path = os.path.join(depth_output_path, f'output_{index}.pickle')
    with open(file_path, 'ab') as f:
        while True:
            # Wait for a coherent pair of frames: depth and color
            frames = pipeline.wait_for_frames()
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            if not depth_frame or not color_frame:
                continue

            # Convert images to numpy arrays
            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())

            real_depth = depth_image * depth_scale
            print(real_depth[200,200])
            # Save this
            # print("real_depth", real_depth)
            # print("max _depth:", real_depth.max())
            # Flatten the matrix into a 1D array
            # flattened_matrix = real_depth.flatten()

            # Sort the flattened array in descending order
            # sorted_array = np.sort(flattened_matrix)[::-1]

            # Print the maximum 10 elements
            # print(sorted_array[:20])
            # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
            depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

            # Write the RGB frame to the MP4 video file
            rgb_video_writer.write(color_image)

            # Convert the depth_image to grayscale
            depth_image_gray = cv2.convertScaleAbs(depth_image, alpha=0.03)

            # # Save the grayscale depth_image as a pickle file
            # pickle_filename = f'depth_image_{frame_number:04d}.pkl'
            # pickle_filepath = os.path.join(depth_output_path, pickle_filename)
            # with open(pickle_filepath, 'wb') as f:
            #     pickle.dump(real_depth, f)
            
            if timeflag:
                ntp_time, time_difference = get_ntp_time_and_difference()
                fake_ntp_timestamp = ntp_time
                logger.info("Using NTP time as the start timmer.")
                timeflag = False
            else:
                current_local_time = datetime.now()
                fake_ntp_timestamp = get_fake_ntp_time(current_local_time, time_difference)
                logger.info("Using the local timmer to pretend to be NTP time. Data recorded")
            # Create a dictionary containing the timestamp and frame data
            depth_img = {
                'timestamp': fake_ntp_timestamp,
                'depth_image': real_depth
            }

            # Save the dictionary to a pickle file
    
            save_timestamp_data_modified(real_depth, fake_ntp_timestamp, f)
            # Save frame data and timestamp
            # print("fake_ntp_timestamp", fake_ntp_timestamp)

            # To calculate the actual sampling rate
            sampler.update_loop()
            # Calculate the total frame
            frame_counter += 1
            # Append the timestamp to the respective lists
            depth_image_timestamps.append(fake_ntp_timestamp)
            rgb_video_timestamps.append(fake_ntp_timestamp)
            # Increment the frame number
            frame_number += 1

            # Show images
            cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
            cv2.imshow('RealSense', np.hstack((color_image, depth_colormap)))
            cv2.waitKey(1)
            if cv2.waitKey(1) == 27 or check_terminate_flag():
                logger.info("End recording by a terminate action.")
                # Check the size of the saved MP4 video and pickle file
                mp4_size = os.path.getsize(rgb_video_filename)
                human_readable_mp4_size = convert_size(mp4_size)
                pickle_size = os.path.getsize(file_path)
                human_readable_size = convert_size(pickle_size)
                with open(os.path.join(os.path.dirname(__file__), "deptcam_data_saved_status.txt"), "w") as f:
                        f.write(f"Deptcam Data saved /DeptCam/output_{index}/depth_image_output_{index}.pickle,\n")
                        f.write(f"RBG video saved /DeptCam/output_{index}/rgb_video_output_{index}/rgb_video.mp4,\n")
                        f.write(f"Depthcam Log saved /DeptCam/logs/config_{index}.log\n")
                        f.write(f"Total frames processed: {frame_counter},\n")
                        f.write(f"DepthCam Pickle file size: {human_readable_size},\n")
                        f.write(f"RGB Video file size: {human_readable_mp4_size}.\n")
                break
    # while True:
    #     # Wait for a coherent pair of frames: depth and color
    #     frames = pipeline.wait_for_frames()
    #     depth_frame = frames.get_depth_frame()
    #     color_frame = frames.get_color_frame()
    #     if not depth_frame or not color_frame:
    #         continue

    #     # Convert images to numpy arrays
    #     depth_image = np.asanyarray(depth_frame.get_data())
    #     color_image = np.asanyarray(color_frame.get_data())

    #     real_depth = depth_image * depth_scale
    #     print(real_depth[200,200])
    #     # Save this
    #     # print("real_depth", real_depth)
    #     # print("max _depth:", real_depth.max())
    #     # Flatten the matrix into a 1D array
    #     # flattened_matrix = real_depth.flatten()

    #     # Sort the flattened array in descending order
    #     # sorted_array = np.sort(flattened_matrix)[::-1]

    #     # Print the maximum 10 elements
    #     # print(sorted_array[:20])
    #     # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
    #     depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

    #     # Write the RGB frame to the MP4 video file
    #     rgb_video_writer.write(color_image)

    #     # Convert the depth_image to grayscale
    #     depth_image_gray = cv2.convertScaleAbs(depth_image, alpha=0.03)

    #     # Save the grayscale depth_image as a pickle file
    #     pickle_filename = f'depth_image_{frame_number:04d}.pkl'
    #     pickle_filepath = os.path.join(depth_output_path, pickle_filename)
    #     # with open(pickle_filepath, 'wb') as f:
    #     #     pickle.dump(real_depth, f)
        
    #     if timeflag:
    #         ntp_time, time_difference = get_ntp_time_and_difference()
    #         fake_ntp_timestamp = ntp_time
    #         timeflag = False
    #     else:
    #         current_local_time = datetime.now()
    #         fake_ntp_timestamp = get_fake_ntp_time(current_local_time, time_difference)
    #         logger.info("Using the local timmer to pretend to be NTP time. Data recorded")
    #     # Create a dictionary containing the timestamp and frame data
    #     depth_img = {
    #         'timestamp': fake_ntp_timestamp,
    #         'depth_image': real_depth
    #     }

    #     # Save the dictionary to a pickle file
    #     with open(pickle_filepath, 'wb') as f:
    #         pickle.dump(depth_img, f)
    #     # Save frame data and timestamp
    #     # print("fake_ntp_timestamp", fake_ntp_timestamp)

    #     # To calculate the actual sampling rate
    #     sampler.update_loop()

    #     # Append the timestamp to the respective lists
    #     depth_image_timestamps.append(fake_ntp_timestamp)
    #     rgb_video_timestamps.append(fake_ntp_timestamp)
    #     # Increment the frame number
    #     frame_number += 1

    #     # Show images
    #     cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
    #     cv2.imshow('RealSense', np.hstack((color_image, depth_colormap)))
    #     cv2.waitKey(1)
    #     if cv2.waitKey(1) == 27 or check_terminate_flag():
    #         logger.info("End recording by a terminate action.")
    #         break


    # Release the video writer
    rgb_video_writer.release()

finally:
    # Save the timestamp lists to separate files
    with open(os.path.join(main_output_path, 'timestamps.txt'), 'w') as f:
        for timestamp in rgb_video_timestamps:
            f.write(f"{timestamp}\n")

    # with open(os.path.join(depth_output_path, 'depth_image_timestamps.txt'), 'w') as f:
    #     for timestamp in depth_image_timestamps:
    #         f.write(f"{timestamp}\n")
    # Stop streaming
    # cv2.destroyWindow('RealSense')
    pipeline.stop()