from config import play_arg, process_arg, global_arg
from audio.audio import AudioRecorder
from time import sleep
from loguru import logger
import os
# For receiving the termination signal from the streamlit
def check_terminate_flag():
    if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '../terminate_flag.txt')))or os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '../terminate_ira_flag.txt'))):
        # os.remove("terminate_flag.txt")
        return True
    return False

logger.info("Delay {}s".format(global_arg.delay))
sleep(global_arg.delay)
recorder = AudioRecorder(play_arg, path=global_arg.data_path)

if recorder:
    logger.info("Start Recording ...")
    print("Recording started. Press Ctrl+C to stop.")
    recorder.begin()
    try:
        print("Recording started. Waiting for termination signal or press Ctrl+C to stop.")
        while True:
            if check_terminate_flag():
                print("Termination signal received. Stopping recording.")
                break
            sleep(1)  # Sleep for a short time to avoid busy waiting
    except KeyboardInterrupt:
        print("Recording stopped by Ctrl+C.")
    finally:
        # Stop recording
        data_record = recorder.get_record()
        print(f"Data shape: {data_record.shape}")
        if global_arg.set_save:
            recorder.save_record()
        recorder.end()
        