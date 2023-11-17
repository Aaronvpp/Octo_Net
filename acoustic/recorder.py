from config import play_arg, process_arg, global_arg
from acoustic.audio.audio import AudioRecorder
from time import sleep
from loguru import logger

logger.info("Delay {}s".format(global_arg.delay))
sleep(global_arg.delay)
recorder = AudioRecorder(play_arg)

if recorder:
    logger.info("Start Recording ...")
    try:
        while True:
            recorder.begin()
    except KeyboardInterrupt:
        logger.info("Stop Recorder ...")
        data_record = recorder.get_record()
        if global_arg.set_save:
            recorder.save_record()
        # player.end()
        recorder.end()
