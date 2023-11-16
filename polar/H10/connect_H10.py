from PolarH10 import PolarH10
from bleak import BleakScanner
import numpy as np
from matplotlib import pyplot as plt
import asyncio
from tqdm import tqdm
from datetime import datetime
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from time_utils import *
from save_timestamp_data import *
from log_utils import *
from sampling_rate import SamplingRateCalculator
import configparser
import json
import asyncio
from bleak import BleakScanner

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
    if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../terminate_flag.txt'))) or os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../terminate_polar_flag.txt'))):
        # os.remove("terminate_flag.txt")
        return True
    return False

async def main():
        # Calculate the actual sampling rate
        sampler = SamplingRateCalculator("Polar")
        # Initialize the frame to calculate the total frame
        frame_counter = 0
        devices = await BleakScanner.discover()
        # Initial config.ini
        config = configparser.ConfigParser()
        config.read(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../config.ini')))
        polar_settings_str = config.get('device_settings', 'polar')
        polar_settings = json.loads(polar_settings_str)
        # General setting
        output_directory = os.path.dirname(os.path.abspath(__file__))
        current_index = get_next_index_polar(output_directory)
        # Log 
        logger = setup_logger(output_directory, current_index)
        config_data = {}
        for section in config.sections():
            if section != 'device_settings':
                config_data[section] = dict(config.items(section))
        logger.info(f"Loaded configuration: {config_data}")
        logger.info(f"Loaded Polar configuration: {polar_settings}")
        # seekthermal_settings_str = config.get('device_settings', 'polar')
        # config_data = {}
        # for section in config.sections():
        #     if section != 'device_settings':
        #         config_data[section] = dict(config.items(section))
        # logger.info(f"Loaded configuration: {config_data}")
        # logger.info(f"Loaded IRA configuration: {polar_settings}")
        record_len = int(polar_settings["record_len(in_second)"])
        for device in devices:
            timeflag = True
            if device.name is not None and "Polar" in device.name:
                print("Find Polar H10!")
                polar_device = PolarH10(device)
                await polar_device.connect()
                
                try:
                    await polar_device.get_device_info()
                    await polar_device.print_device_info()
                    # await polar_device.start_ecg_stream()
                    await polar_device.start_hr_stream()
                    # try:
                    # Using a flag file to tell other modalities they can start
                    with open('polar_ready.txt', 'w') as file:
                        file.write("Polar H10 is ready")

                    for i in tqdm(range(record_len), desc='Recording...'):
                        current_local_time = datetime.now()
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

                        # acc_data = polar_device.get_acc_data()
                        # ecg_data = polar_device.get_ecg_data()
                        # logger.info("ecg_data", ecg_data)
                        # print("ecg_data", ecg_data)
                        # save_timestamp_data_polar(ecg_data, current_index, fake_ntp_timestamp, output_directory, "ecg_data")
                        # ibi_data = polar_device.get_ibi_data()
                        hr_data = polar_device.get_hr_data()
                        print("get_hr_data", hr_data)
                        logger.info("get_hr_data", hr_data)
                        file_path =save_timestamp_data_polar(hr_data, current_index, fake_ntp_timestamp, output_directory)
                        # To calculate the actual sampling rate
                        sampler.update_loop()
                        # Calculate the total frame
                        frame_counter += 1
                        await asyncio.sleep(1)
                        

                        if check_terminate_flag():
                            logger.info("End recording by a terminate action.")
                            pickle_size = os.path.getsize(file_path)
                            human_readable_size = convert_size(pickle_size)
                            with open(os.path.join(os.path.dirname(__file__), "polar_data_saved_status.txt"), "w") as f:
                                f.write(f"Polar Data saved /polar/H10/data/output_{current_index}.pickle,\n")
                                f.write(f"Polar Log saved /polar/H10/logs/config_{current_index}.log\n")
                                f.write(f"Total frames processed: {frame_counter},\n")
                                f.write(f"Pickle file size: {human_readable_size}\n")
                            if os.path.exists('polar_ready.txt'):
                                os.remove('polar_ready.txt')
                
                            break

                    # except KeyboardInterrupt:
                    #     logger.info("End recording by a KeyboardInterrupt.") 
                
                    # await polar_device.stop_ecg_stream()
                    await polar_device.stop_hr_stream()
                    pickle_size = os.path.getsize(file_path)
                    human_readable_size = convert_size(pickle_size)
                    with open(os.path.join(os.path.dirname(__file__), "polar_data_saved_status.txt"), "w") as f:
                        f.write(f"Polar Data saved /polar/H10/data/output_{current_index}.pickle,\n")
                        f.write(f"Polar Log saved /polar/H10/logs/config_{current_index}.log\n")
                        f.write(f"Total frames processed: {frame_counter},\n")
                        f.write(f"Pickle file size: {human_readable_size}\n")
                finally:
                    await polar_device.disconnect()
                    if os.path.exists('polar_ready.txt'):
                        os.remove('polar_ready.txt')
                    
                    
            else:
                logger.error("Polar H10 device not found. ")
                print("Polar H10 device not found. ")




if __name__ == "__main__":
    asyncio.run(main())
