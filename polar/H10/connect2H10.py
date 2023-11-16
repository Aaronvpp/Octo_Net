'''script to connect to Polar H10 and record BR
'''
from .PolarH10 import PolarH10
from bleak import BleakScanner
import numpy as np
from matplotlib import pyplot as plt
import asyncio
from tqdm import tqdm
from loguru import logger


async def discover_device():
    return await BleakScanner.discover()


async def connectH10(polar_device):
    await polar_device.connect()
    await polar_device.get_device_info()
    await polar_device.print_device_info()


async def start_acc_stream(polar_device):
    await polar_device.start_acc_stream()


async def start_hr_stream(polar_device):
    await polar_device.start_hr_stream()


async def stop_acc_stream(polar_device):
    await polar_device.stop_acc_stream()


async def stop_hr_stream(polar_device):
    await polar_device.stop_hr_stream()


def get_acc_data(polar_device):
    return polar_device.get_acc_data()


def get_hr_data(polar_device):
    return polar_device.get_hr_data()


def get_ibi_data(polar_device):
    return polar_device.get_ibi_data()


async def disconnectH10(polar_device):
    await polar_device.disconnect()

# record_len = 30
# for device in devices:
#     if device.name is not None and "Polar" in device.name:
#         print("Find Polar H10!")
#         polar_device = PolarH10(device)
#         await polar_device.connect()
#         await polar_device.get_device_info()
#         await polar_device.print_device_info()
#         await polar_device.start_acc_stream()
#         await polar_device.start_hr_stream()
#         for i in tqdm(range(record_len), desc='Recording...'):
#             await asyncio.sleep(1)
#         await polar_device.stop_acc_stream()
#         await polar_device.stop_hr_stream()

#         acc_data = polar_device.get_acc_data()
#         ibi_data = polar_device.get_ibi_data()
#         hr_data = polar_device.get_hr_data()
#         await polar_device.disconnect()


async def main():
    record_len = 30
    devices = await discover_device()
    for device in devices:
        if device.name is not None and "Polar" in device.name:
            print("Find Polar H10!")
            polar_device = PolarH10(device)
            await polar_device.connect()
            try:
                await polar_device.get_device_info()
                await polar_device.print_device_info()
                await polar_device.start_ecg_stream()
                await polar_device.start_hr_stream()
                for i in tqdm(range(record_len), desc='Recording...'):
                    await asyncio.sleep(1)
                await polar_device.stop_ecg_stream()
                await polar_device.stop_hr_stream()

                # acc_data = polar_device.get_acc_data()
                ecg_data = polar_device.get_ecg_data()
                # ibi_data = polar_device.get_ibi_data()
                hr_data = polar_device.get_hr_data()
            finally:
                await polar_device.disconnect()

                break
    else:
        logger.error("No Polar H10 found!")

    hr_data = np.array(hr_data)
    ecg_data = np.array(ecg_data)
    plt.plot(hr_data["times"], hr_data["values"])
    plt.plot(ecg_data["times"], ecg_data["values"])

if __name__ == "__main__":
    asyncio.run(main())
