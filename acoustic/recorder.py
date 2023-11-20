from config import play_arg, process_arg, global_arg
from audio.audio import AudioRecorder
from time import sleep
from loguru import logger

logger.info("Delay {}s".format(global_arg.delay))
sleep(global_arg.delay)
recorder = AudioRecorder(play_arg, path=global_arg.data_path)

if recorder:
    logger.info("Start Recording ...")
    try:
        print("Recording started. Press Ctrl+C to stop.")
        recorder.begin()
        while True:
            # Endless loop for recording. It will keep recording until KeyboardInterrupt is raised.
            pass
    except KeyboardInterrupt:
        # Stop recording when Ctrl+C is pressed
        print("Recording stopped.")
        data_record = recorder.get_record()
        print(f"Data shape: {data_record.shape}")
        if global_arg.set_save:
            recorder.save_record()
        recorder.end()
        