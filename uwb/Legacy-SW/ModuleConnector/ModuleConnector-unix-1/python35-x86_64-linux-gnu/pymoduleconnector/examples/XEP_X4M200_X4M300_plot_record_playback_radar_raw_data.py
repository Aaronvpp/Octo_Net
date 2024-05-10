# #!/usr/bin/env python
# """ \example XEP_X4M200_X4M300_plot_record_playback_radar_raw_data.py

# #Target module: X4M200,X4M300,X4M03

# #Introduction: XeThru modules support both RF and baseband data output. This is an example of radar raw data manipulation. 
#                Developer can use Module Connecter API to read, record radar raw data, and also playback recorded data. 
			   
# #Command to run: "python XEP_X4M200_X4M300_plot_record_playback_radar_raw_data.py -d com8" or "python3 X4M300_printout_presence_state.py -d com8"
#                  change "com8" with your device name, using "--help" to see other options.
#                  Using TCP server address as device name is also supported, e.g. 
#                  "python X4M200_sleep_record.py -d tcp://192.168.1.169:3000".
# """

# from __future__ import print_function, division
# import pickle
# import sys
# from optparse import OptionParser
# from time import sleep
# import os
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../..')))
# from time_utils import *
# from log_utils import *
# from save_timestamp_data import get_next_index
# from sampling_rate import *
# import numpy as np
# import matplotlib.pyplot as plt
# from matplotlib.animation import FuncAnimation
# import math
# import pymoduleconnector
# from pymoduleconnector import DataType
# import time

# __version__ = 3
# # For receiving the termination signal from the streamlit
# def check_terminate_flag():
#     if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../../terminate_flag.txt'))) or os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../terminate_seek_flag.txt'))):
#         # os.remove("terminate_flag.txt")
#         return True
#     return False

# # To see the size of the saved pickle
# def convert_size(size_bytes):
#     if size_bytes == 0:
#         return "0B"
#     size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
#     i = int(math.floor(math.log(size_bytes, 1024)))
#     p = math.pow(1024, i)
#     s = round(size_bytes / p, 2)
#     return "{:.2f} {}".format(s, size_name[i])

# def reset(device_name):
#     mc = pymoduleconnector.ModuleConnector(device_name)
#     xep = mc.get_xep()
#     xep.module_reset()
#     mc.close()
#     sleep(3)

# def on_file_available(data_type, filename):
#     print("new file available for data type: {}".format(data_type))
#     print("  |- file: {}".format(filename))
#     if data_type == DataType.FloatDataType:
#         print("processing Float data from file")

# def on_meta_file_available(session_id, meta_filename):
#     print("new meta file available for recording with id: {}".format(session_id))
#     print("  |- file: {}".format(meta_filename))

# def clear_buffer(mc):
#     """Clears the frame buffer"""
#     xep = mc.get_xep()
#     while xep.peek_message_data_float():
#         xep.read_message_data_float()

# def simple_xep_plot(device_name, record=False, baseband=False):
#     FPS = 10
#     directory = '.'
#     reset(device_name)
#     mc = pymoduleconnector.ModuleConnector(device_name)
#     output_directory = os.path.dirname(os.path.abspath(__file__))
#     # pickle_idx = 0
#     experiment_idx = get_next_index(output_directory)
#     data_folder = os.path.join(output_directory, "data")
#     if not os.path.exists(data_folder):
#         os.makedirs(data_folder)
        
#     file_path = os.path.join(data_folder, 'output_{}.pickle'.format(experiment_idx))
#     logger = setup_logger(output_directory, experiment_idx)
#     with open(file_path, 'ab') as f:
        
#         timeflag = True
#         # Calculate the actual sampling rate
#         sampler = SamplingRateCalculator("uwb")
#         # Initialize the frame to calculate the total frame
#         frame_counter_uwb = 0
#         # Assume an X4M300/X4M200 module and try to enter XEP mode
#         app = mc.get_x4m300()
#         # Stop running application and set module in manual mode.
#         try:
#             app.set_sensor_mode(0x13, 0) # Make sure no profile is running.
#         except RuntimeError:
#             # Profile not running, OK
#             pass

#         try:
#             app.set_sensor_mode(0x12, 0) # Manual mode.
#         except RuntimeError:
#             # Maybe running XEP firmware only?
#             pass

#         if record:
#             recorder = mc.get_data_recorder()
#             recorder.subscribe_to_file_available(pymoduleconnector.AllDataTypes, on_file_available )
#             recorder.subscribe_to_meta_file_available(on_meta_file_available)

#         xep = mc.get_xep()
#         # Set DAC range
#         xep.x4driver_set_dac_min(900)
#         xep.x4driver_set_dac_max(1150)

#         # Set integration
#         xep.x4driver_set_iterations(16)
#         xep.x4driver_set_pulses_per_step(26)

#         xep.x4driver_set_downconversion(int(baseband))
#         # Start streaming of data
#         xep.x4driver_set_fps(FPS)
#         # xep.x4driver_set_frame_area_offset(0)
#         xep.x4driver_set_frame_area(0,10)

#         def read_frame(f,timeflag):
#             """Gets frame data from module"""
#             d = xep.read_message_data_float()
#             frame = np.array(d.data)
#             # Convert the resulting frame to a complex array if downconversion is enabled
#             if baseband:
#                 n = len(frame)
#                 frame = frame[:n//2] + 1j*frame[n//2:]

#             # if timeflag:
#             ntp_time, time_difference = get_ntp_time_and_difference()
#             fake_ntp_timestamp = ntp_time
#             logger.info("Using NTP timer.")
#                 # timeflag = False
#             # else:
#             #     current_local_time = datetime.now()
#             #     fake_ntp_timestamp = get_fake_ntp_time(current_local_time, time_difference)
#             #     logger.info("Using the local timmer to pretend to be NTP time. Data recorded")
#             # Get the current timestamp
#             timestamp = fake_ntp_timestamp 
            
#             # Save the timestamp and frame to a dictionary
#             frame_data = {"timestamp": timestamp, "frame": frame.tolist()}
#             print("timestamp", timestamp)
#             pickle.dump(frame_data, f)
#             return frame

        
#         def animate(i):
#             nonlocal frame_counter_uwb
#             if check_terminate_flag():
#                 print("Termination signal received. Closing animation.")
#                 plt.close(fig)  # This will close the figure and end the animation loop
#                 logger.info("End recording by a terminate action.")
#                 pickle_size = os.path.getsize(file_path)
#                 human_readable_size = convert_size(pickle_size)
#                 with open(os.path.join(os.path.dirname(__file__), "uwb_data_saved_status.txt"), "w") as h:
#                     h.write("uwb Data saved data/output_{}.pickle,\n".format(experiment_idx))
#                     h.write("uwb Log saved logs/config_{}.log\n".format(experiment_idx))
#                     h.write("Total frames processed: {},\n".format(frame_counter_uwb))
#                     h.write("Pickle file size: {}\n".format(human_readable_size))
#                 return
            
#             # To calculate the actual sampling rate
#             sampler.update_loop()
#             # Calculate the total frame
#             frame_counter_uwb += 1
#             if baseband:
#                 line.set_ydata(abs(read_frame(f, timeflag))) # update the data
#             else:
#                 line.set_ydata(read_frame(f, timeflag))
#             return line,

#         fig = plt.figure(num=55)
#         fig.suptitle("example version %d "%(__version__))
#         ax = fig.add_subplot(1,1,1)
#         ax.set_ylim(0 if baseband else -0.03,0.03) #keep graph in frame (FIT TO YOUR DATA)
#         frame = read_frame(f,timeflag)
#         if baseband:
#             frame = abs(frame)
#         line, = ax.plot(frame)

#         clear_buffer(mc)

#         if record:
#             recorder.start_recording(DataType.BasebandApDataType | DataType.FloatDataType, directory)

#         ani = FuncAnimation(fig, animate, interval=FPS)
#         try:
#             plt.show()
#         finally:
#             # Stop streaming of data
#             xep.x4driver_set_fps(0)

# # def playback_recording(meta_filename, baseband=False):
# #     print("Starting playback for {}" .format(meta_filename))
# #     player = pymoduleconnector.DataPlayer(meta_filename, -1)
# #     dur = player.get_duration()
# #     mc = pymoduleconnector.ModuleConnector(player)
# #     xep = mc.get_xep()
# #     player.set_playback_rate(1.0)
# #     player.set_loop_mode_enabled(True)
# #     player.play()

# #     print("Duration(ms): {}".format(dur))

# #     def read_frame():
# #         """Gets frame data from module"""
# #         d = xep.read_message_data_float()
# #         frame = np.array(d.data)
# #         if baseband:
# #             n = len(frame)
# #             frame = frame[:n//2] + 1j*frame[n//2:]
# #         return frame

# #     def animate(i):
# #         if baseband:
# #             line.set_ydata(abs(read_frame()))  # update the data
# #         else:
# #             line.set_ydata(read_frame())
# #         return line,

# #     fig = plt.figure()
# #     fig.suptitle("Plot playback")
# #     ax = fig.add_subplot(1,1,1)
# #     frame = read_frame()
# #     line, = ax.plot(frame)
# #     ax.set_ylim(0 if baseband else -0.03,0.03) #keep graph in frame (FIT TO YOUR DATA)
# #     ani = FuncAnimation(fig, animate, interval=10)
# #     plt.show()

# #     player.stop()

# def main():
#     parser = OptionParser()
#     parser.add_option(
#         "-d",
#         "--device",
#         dest="device_name",
#         help="device file to use",
#         metavar="FILE")
#     parser.add_option(
#         "-b",
#         "--baseband",
#         action="store_true",
#         default=False,
#         dest="baseband",
#         help="Enable baseband, rf data is default")
#     parser.add_option(
#         "-r",
#         "--record",
#         action="store_true",
#         default=False,
#         dest="record",
#         help="Enable recording")
#     parser.add_option(
#         "-f",
#         "--file",
#         dest="meta_filename",
#         metavar="FILE",
#         help="meta file from recording")

#     (options, args) = parser.parse_args()
#     if not options.device_name:
#         if  options.meta_filename:
#             # playback_recording(options.meta_filename,
#             #         baseband=options.baseband)
#             pass
#         else:
#             parser.error("Missing -d or -f. See --help.")
#     else:
#         simple_xep_plot(options.device_name, record=options.record,
#                 baseband=options.baseband)

# if __name__ == "__main__":
#    main()
#!/usr/bin/env python
""" \example XEP_X4M200_X4M300_plot_record_playback_radar_raw_data.py

#Target module: X4M200,X4M300,X4M03

#Introduction: XeThru modules support both RF and baseband data output. This is an example of radar raw data manipulation. 
               Developer can use Module Connecter API to read, record radar raw data, and also playback recorded data. 
			   
#Command to run: "python XEP_X4M200_X4M300_plot_record_playback_radar_raw_data.py -d com8" or "python3 X4M300_printout_presence_state.py -d com8"
                 change "com8" with your device name, using "--help" to see other options.
                 Using TCP server address as device name is also supported, e.g. 
                 "python X4M200_sleep_record.py -d tcp://192.168.1.169:3000".
"""

from __future__ import print_function, division
import pickle
import sys
from optparse import OptionParser
from time import sleep
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../..')))
from time_utils import *
from log_utils import *
from save_timestamp_data import get_next_index
from sampling_rate import *
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import math
import pymoduleconnector
from pymoduleconnector import DataType
import time
import json
import configparser

__version__ = 3
# For receiving the termination signal from the streamlit
def check_terminate_flag():
    if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../../terminate_flag.txt'))) or os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../terminate_seek_flag.txt'))):
        # os.remove("terminate_flag.txt")
        return True
    return False

# To see the size of the saved pickle
def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "{:.2f} {}".format(s, size_name[i])

def reset(device_name):
    mc = pymoduleconnector.ModuleConnector(device_name)
    xep = mc.get_xep()
    xep.module_reset()
    mc.close()
    sleep(3)

def on_file_available(data_type, filename):
    print("new file available for data type: {}".format(data_type))
    print("  |- file: {}".format(filename))
    if data_type == DataType.FloatDataType:
        print("processing Float data from file")

def on_meta_file_available(session_id, meta_filename):
    print("new meta file available for recording with id: {}".format(session_id))
    print("  |- file: {}".format(meta_filename))

def clear_buffer(mc):
    """Clears the frame buffer"""
    xep = mc.get_xep()
    while xep.peek_message_data_float():
        xep.read_message_data_float()

def simple_xep_plot(device_name, record=False, baseband=False):
    FPS = 17
    directory = '.'
    # reset(device_name)
    mc = pymoduleconnector.ModuleConnector(device_name)
    output_directory = os.path.dirname(os.path.abspath(__file__))
    # pickle_idx = 0
    experiment_idx = get_next_index(output_directory)
    data_folder = os.path.join(output_directory, "data")
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
        
    
    
    config = configparser.ConfigParser()
    config.read(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../../config.ini')))
    
    # Modify the naming protocode
    participant_id = config.get('participant', 'id')
    trial_number = config.get('task_info', 'trial_number')
    activity = config.get('label_info', 'activity')
    starttimestamp, _ = get_ntp_time_and_difference()
    # Format the timestamp to exclude microseconds (down to seconds)
    starttimestamp = starttimestamp.strftime("%Y%m%d%H%M%S")
    file_name = "{}_node_1_modality_uwb_subject_{}_activity_{}_trial_{}".format(starttimestamp, participant_id, activity, trial_number)
    
    file_path = os.path.join(data_folder, '{}.pickle'.format(file_name))
    logger = setup_logger(output_directory, file_name)
    uwb_settings_str = config.get('device_settings', 'uwb')
    uwb_settings = json.loads(uwb_settings_str)
    min_dist = uwb_settings['min_distance']
    max_dist = uwb_settings['max_distance']
    config_data = {}
    for section in config.sections():
        if section != 'device_settings':
            config_data[section] = dict(config.items(section))
    logger.info("Loaded configuration: {}".format(config_data))
    logger.info("Loaded UWB configuration: {}".format(uwb_settings))
    with open(file_path, 'ab') as f:
        
        timeflag = True
        # Calculate the actual sampling rate
        sampler = SamplingRateCalculator("uwb")
        # Initialize the frame to calculate the total frame
        frame_counter_uwb = 0
        # Assume an X4M300/X4M200 module and try to enter XEP mode
        app = mc.get_x4m300()
        # Stop running application and set module in manual mode.
        try:
            app.set_sensor_mode(0x13, 0) # Make sure no profile is running.
        except RuntimeError:
            # Profile not running, OK
            pass

        try:
            app.set_sensor_mode(0x12, 0) # Manual mode.
        except RuntimeError:
            # Maybe running XEP firmware only?
            pass

        if record:
            recorder = mc.get_data_recorder()
            recorder.subscribe_to_file_available(pymoduleconnector.AllDataTypes, on_file_available )
            recorder.subscribe_to_meta_file_available(on_meta_file_available)

        xep = mc.get_xep()
        # Set DAC range
        xep.x4driver_set_dac_min(900)
        xep.x4driver_set_dac_max(1150)

        # Set integration
        xep.x4driver_set_iterations(16)
        xep.x4driver_set_pulses_per_step(26)

        xep.x4driver_set_downconversion(int(baseband))
        # Start streaming of data
        xep.x4driver_set_fps(FPS)
        xep.x4driver_set_frame_area_offset(0)
        xep.x4driver_set_frame_area(float(min_dist),float(max_dist))    
        print((xep.x4driver_get_tx_center_frequency()),'ep.x4driver_get_tx_center_frequency')
        def read_frame(f,timeflag):
            """Gets frame data from module"""
            d = xep.read_message_data_float()
            frame = np.array(d.data)
            # Convert the resulting frame to a complex array if downconversion is enabled
            if baseband:
                n = len(frame)
                frame = frame[:n//2] + 1j*frame[n//2:]

            # if timeflag:
            ntp_time, time_difference = get_ntp_time_and_difference()
            fake_ntp_timestamp = ntp_time
            logger.info("Using NTP timer.")
                # timeflag = False
            # else:
            #     current_local_time = datetime.now()
            #     fake_ntp_timestamp = get_fake_ntp_time(current_local_time, time_difference)
            #     logger.info("Using the local timmer to pretend to be NTP time. Data recorded")
            # Get the current timestamp
            timestamp = fake_ntp_timestamp 
            print("frame.shape", frame.shape)
            # Save the timestamp and frame to a dictionary
            frame_data = {"timestamp": timestamp, "frame": frame.tolist()}
            # print("timestamp", timestamp)
            pickle.dump(frame_data, f)
            return frame

        
        def animate(i):
            nonlocal frame_counter_uwb
            if check_terminate_flag():
                print("Termination signal received. Closing animation.")
                plt.close(fig)  # This will close the figure and end the animation loop
                logger.info("End recording by a terminate action.")
                pickle_size = os.path.getsize(file_path)
                human_readable_size = convert_size(pickle_size)
                with open(os.path.join(os.path.dirname(__file__), "uwb_data_saved_status.txt"), "w") as h:
                    h.write("uwb Data saved /uwb/data/{}.pickle,\n".format(file_name))
                    h.write("uwb Log saved /uwb/logs/{}.log\n".format(file_name))
                    h.write("Total frames processed: {},\n".format(frame_counter_uwb))
                    h.write("Pickle file size: {}\n".format(human_readable_size))
                return
            
            # To calculate the actual sampling rate
            sampler.update_loop()
            # Calculate the total frame
            frame_counter_uwb += 1
            if baseband:
                line.set_ydata(abs(read_frame(f, timeflag))) # update the data
            else:
                line.set_ydata(read_frame(f, timeflag))
            return line,

        fig = plt.figure(num=55)
        fig.suptitle("example version %d "%(__version__))
        ax = fig.add_subplot(1,1,1)
        ax.set_ylim(0 if baseband else -0.03,0.03) #keep graph in frame (FIT TO YOUR DATA)
        frame = read_frame(f,timeflag)
        if baseband:
            frame = abs(frame)
        line, = ax.plot(frame)

        clear_buffer(mc)

        if record:
            recorder.start_recording(DataType.BasebandApDataType | DataType.FloatDataType, directory)

        ani = FuncAnimation(fig, animate, interval=FPS)
        try:
            plt.show()
        finally:
            # Stop streaming of data
            xep.x4driver_set_fps(0)

# def playback_recording(meta_filename, baseband=False):
#     print("Starting playback for {}" .format(meta_filename))
#     player = pymoduleconnector.DataPlayer(meta_filename, -1)
#     dur = player.get_duration()
#     mc = pymoduleconnector.ModuleConnector(player)
#     xep = mc.get_xep()
#     player.set_playback_rate(1.0)
#     player.set_loop_mode_enabled(True)
#     player.play()

#     print("Duration(ms): {}".format(dur))

#     def read_frame():
#         """Gets frame data from module"""
#         d = xep.read_message_data_float()
#         frame = np.array(d.data)
#         if baseband:
#             n = len(frame)
#             frame = frame[:n//2] + 1j*frame[n//2:]
#         return frame

#     def animate(i):
#         if baseband:
#             line.set_ydata(abs(read_frame()))  # update the data
#         else:
#             line.set_ydata(read_frame())
#         return line,

#     fig = plt.figure()
#     fig.suptitle("Plot playback")
#     ax = fig.add_subplot(1,1,1)
#     frame = read_frame()
#     line, = ax.plot(frame)
#     ax.set_ylim(0 if baseband else -0.03,0.03) #keep graph in frame (FIT TO YOUR DATA)
#     ani = FuncAnimation(fig, animate, interval=10)
#     plt.show()

#     player.stop()

def main():
    parser = OptionParser()
    parser.add_option(
        "-d",
        "--device",
        dest="device_name",
        help="device file to use",
        metavar="FILE")
    parser.add_option(
        "-b",
        "--baseband",
        action="store_true",
        default=False,
        dest="baseband",
        help="Enable baseband, rf data is default")
    parser.add_option(
        "-r",
        "--record",
        action="store_true",
        default=False,
        dest="record",
        help="Enable recording")
    parser.add_option(
        "-f",
        "--file",
        dest="meta_filename",
        metavar="FILE",
        help="meta file from recording")

    (options, args) = parser.parse_args()
    if not options.device_name:
        if  options.meta_filename:
            # playback_recording(options.meta_filename,
            #         baseband=options.baseband)
            pass
        else:
            parser.error("Missing -d or -f. See --help.")
    else:
        simple_xep_plot(options.device_name, record=options.record,
                baseband=options.baseband)

if __name__ == "__main__":
   main()