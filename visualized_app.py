import os
import streamlit as st
import cv2
import numpy as np
import pickle
from datetime import datetime
import matplotlib.pyplot as plt
import glob
import re
# Define the SubpageInterpolating function
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
                num += 1
            except IndexError:
                top = 0.0
            
            try:
                down = mat[i+1,j]
                num += 1
            except IndexError:
                down = 0.0
            
            try:
                left = mat[i,j-1]
                num += 1
            except IndexError:
                left = 0.0
            
            try:
                right = mat[i,j+1]
                num += 1
            except IndexError:
                right = 0.0
            
            mat[i,j] = (top + down + left + right)/num if num > 0 else 0.0
    return mat

# Define the function to load data from a pickle file
def load_data_from_pickle(pickle_file):
    data = []
    with open(pickle_file, 'rb') as f:
        try:
            while True:
                data.append(pickle.load(f))
        except EOFError:
            pass
    return data

# Define the function to display a frame
def display_frame_ira(data, index):
    if index >= len(data):
        st.write(f"Invalid index. Please choose a value between 0 and {len(data) - 1}.")
        return
    
    frame_data = data[index]
    timestamp = datetime.strptime(frame_data['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
    Detected_temperature = np.array(frame_data['Detected_Temperature']).reshape((24,32))
    ira_interpolated = SubpageInterpolating(Detected_temperature)
    ira_norm = ((ira_interpolated - np.min(ira_interpolated)) / (37 - np.min(ira_interpolated))) * 255
    ira_expand = np.repeat(ira_norm, 20, 0)
    ira_expand = np.repeat(ira_expand, 20, 1)
    ira_img_colored = cv2.applyColorMap(ira_expand.astype(np.uint8), cv2.COLORMAP_JET)

    # Convert to RGB and display using Streamlit
    st.image(cv2.cvtColor(ira_img_colored, cv2.COLOR_BGR2RGB), caption=f"Timestamp: {timestamp}")

# Define a function for 3D scatter plot
def plot_3d_scatter_mmwave(data, index):
    if index >= len(data):
        st.write(f"Invalid index. Please choose a value between 0 and {len(data) - 1}.")
        return

    data_entry = data[index]
    timestamp = data_entry['timestamp']
    frame_data = data_entry['data']

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    x = frame_data['x']
    y = frame_data['y']
    z = frame_data['z']

    scatter = ax.scatter(x, y, z)

    # Set axis limits
    ax.set_xlim(-5, 5)
    ax.set_ylim(0, 3)
    ax.set_zlim(-5, 5)

    ax.set_xlabel('X axis')
    ax.set_ylabel('Y axis')
    ax.set_zlabel('Z axis')
    ax.set_title(f'3D Scatter Plot at Timestamp: {timestamp}')

    st.pyplot(fig)

# Streamlit UI setup
st.title('Data Visualization')

# IRA Data Visualization
st.header("IRA Visualization")
ira_output_dir = 'IRA/data'  # Update this to your IRA directory path
ira_files = glob.glob(os.path.join(ira_output_dir, 'output_*.pickle'))
ira_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
ira_file_path = st.selectbox('Select an IRA file:', ira_files, key='ira_select')
ira_data = load_data_from_pickle(ira_file_path)
st.write(f"Loaded {len(ira_data)} frames for IRA.")
ira_index = st.slider("Select Frame Index for IRA", 0, len(ira_data) - 1, 0, key='ira_slider')
display_frame_ira(ira_data, ira_index)

# mmWave Data Visualization
st.header("mmWave Visualization")
mmwave_output_dir = 'AWR1843-Read-Data-Python-MMWAVE-SDK-3--master/data'  # Update this to your mmWave directory path
mmwave_files = glob.glob(os.path.join(mmwave_output_dir, 'output_*.pickle'))
mmwave_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
mmwave_file_path = st.selectbox('Select an mmWave file:', mmwave_files, key='mmwave_select')
mmwave_data = load_data_from_pickle(mmwave_file_path)
st.write(f"Loaded {len(mmwave_data)} frames for mmWave.")
mmwave_index = st.slider("Select Frame Index for 3D Scatter", 0, len(mmwave_data) - 1, 0, key='mmwave_slider')
plot_3d_scatter_mmwave(mmwave_data, mmwave_index)


# Depth Cam Video Visualization
st.header("Depth Cam Visualization")
base_depthcam_dir = 'DeptCam'  # Base directory for Depth Cam

# List the available main folders (e.g., output_0, output_1, etc.)
main_folders = glob.glob(os.path.join(base_depthcam_dir, 'output_*'))
main_folder_names = [os.path.basename(folder) for folder in main_folders]
# Function to extract the numerical part from the folder name
def extract_number(folder_name):
    match = re.search(r'\d+$', folder_name)
    return int(match.group()) if match else 0

# Sort the folders by the extracted number in descending order
main_folder_names = sorted([os.path.basename(folder) for folder in main_folders], key=extract_number, reverse=True)
if main_folder_names:
    selected_main_folder = st.selectbox('Select main folder:', main_folder_names, key='main_folder_select')

    # List the available subfolders within the selected main folder
    sub_folders = glob.glob(os.path.join(base_depthcam_dir, selected_main_folder, 'depth_image_output_*'))
    sub_folder_names = [os.path.basename(folder) for folder in sub_folders]
    
    if sub_folder_names:
        selected_sub_folder = st.selectbox('Select subfolder:', sub_folder_names, key='sub_folder_select')

        # Construct the path to the depth video
        depth_video_path = os.path.join(base_depthcam_dir, selected_main_folder, selected_sub_folder, 'depth_video.mp4')

        # Check if the video file exists and display it
        if os.path.exists(depth_video_path):
            video_file = open(depth_video_path,'rb')
            video_bytes = video_file.read()
            st.video(video_bytes)
        else:
            st.write("Depth video file not found.")
    else:
        st.write("No subfolders found in the selected main folder.")
else:
    st.write("No main folders found in the base directory.")

# RGB Video Visualization
st.header("RGB Video Visualization")
base_rgb_dir = 'DeptCam'  # Base directory for RGB videos

# List the available main folders for RGB videos (e.g., output_0, output_1, etc.)
rgb_main_folders = glob.glob(os.path.join(base_rgb_dir, 'output_*'))
rgb_main_folder_names = sorted([os.path.basename(folder) for folder in rgb_main_folders], key=extract_number, reverse=True)

if rgb_main_folder_names:
    selected_rgb_main_folder = st.selectbox('Select RGB main folder:', rgb_main_folder_names, key='rgb_main_folder_select')

    # List the available subfolders within the selected RGB main folder
    rgb_sub_folders = glob.glob(os.path.join(base_rgb_dir, selected_rgb_main_folder, 'rgb_video_output_*'))
    rgb_sub_folder_names = [os.path.basename(folder) for folder in rgb_sub_folders]

    if rgb_sub_folder_names:
        selected_rgb_sub_folder = st.selectbox('Select RGB subfolder:', rgb_sub_folder_names, key='rgb_sub_folder_select')

        # Construct the path to the RGB video file
        rgb_video_path = os.path.join(base_rgb_dir, selected_rgb_main_folder, selected_rgb_sub_folder, 'rgb_video.mp4')

        # Check if the video file exists and display it
        if os.path.exists(rgb_video_path):
            video_file = open(rgb_video_path, 'rb')
            video_bytes = video_file.read()
            st.video(video_bytes)
        else:
            st.write("RGB video file not found.")
    else:
        st.write("No RGB subfolders found in the selected main folder.")
else:
    st.write("No RGB main folders found in the base directory.")


# SeekThermal Cam Video Visualization
st.header("SeekThermal Cam Visualization")
base_seekthermal_dir = 'seekcamera-python/runseek/data'  # Base directory for SeekThermal videos

# List the available thermal video files (e.g., thermal_0.mp4, thermal_1.mp4, etc.)
thermal_files = glob.glob(os.path.join(base_seekthermal_dir, 'thermal_*.mp4'))
thermal_file_names = [os.path.basename(file) for file in thermal_files]
thermal_file_names.sort(key=extract_number,reverse=True)  # Sort the files in descending order

if thermal_file_names:
    selected_thermal_file = st.selectbox('Select a thermal video file:', thermal_file_names, key='thermal_file_select')

    # Construct the path to the selected thermal video file
    thermal_video_path = os.path.join(base_seekthermal_dir, selected_thermal_file)

    # Check if the video file exists and display it
    if os.path.exists(thermal_video_path):
        video_file = open(thermal_video_path, 'rb')
        video_bytes = video_file.read()
        st.video(video_bytes)
    else:
        st.write("Thermal video file not found.")
else:
    st.write("No thermal video files found in the base directory.")
