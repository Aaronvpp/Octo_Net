import time
import json
import os

class SamplingRateCalculator:
    def __init__(self, process_name):
        self.process_name = process_name
        self.loop_start_time = time.time()
        self.loop_count = 0
        self.sampling_rate_update_time = time.time()
        self.file_lock = False

    def acquire_lock(self):
        while self.file_lock:
            time.sleep(0.01)
        self.file_lock = True

    def release_lock(self):
        self.file_lock = False

    def update_loop(self):
        self.loop_count += 1
        loop_end_time = time.time()
        loop_duration = loop_end_time - self.loop_start_time
        self.loop_start_time = loop_end_time

        if time.time() - self.sampling_rate_update_time >= 1:  # Update the sampling rate every second
            sampling_rate = self.loop_count / (time.time() - self.sampling_rate_update_time)
            self.update_sampling_rate(sampling_rate)  # Update the sampling rate in the status.json file
            self.sampling_rate_update_time = time.time()
            self.loop_count = 0

    # def update_sampling_rate(self, sampling_rate):
    #     self.acquire_lock()
    #     with open(os.path.abspath(os.path.join(os.path.dirname(__file__), "status.json")), "r") as f:
    #         status_dict = json.load(f)

    #     status_dict[self.process_name]["sampling_rate"] = sampling_rate

    #     with open(os.path.abspath(os.path.join(os.path.dirname(__file__), "status.json")), "w") as f:
    #         json.dump(status_dict, f)
    #     self.release_lock()

    def update_sampling_rate(self, sampling_rate):
        try:
            with open(os.path.abspath(os.path.join(os.path.dirname(__file__), "status.json")), "r") as f:
                status_dict = json.load(f)
        except json.JSONDecodeError:
            status_dict = {}  # Provide a default value or log an error message

        # Check if the process_name key exists in the status_dict before updating the sampling rate
        if self.process_name in status_dict:
            status_dict[self.process_name]["sampling_rate"] = sampling_rate

            with open(os.path.abspath(os.path.join(os.path.dirname(__file__), "status.json")), "w") as f:
                json.dump(status_dict, f)
        else:
            print(f"Error: {self.process_name} not found in status.json")