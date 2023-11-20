from config import play_arg, process_arg, global_arg
from audio.audio import AudioPlayer, AudioPlayandRecord
from time import sleep
from loguru import logger

logger.info("Delay {}s".format(global_arg.delay))
sleep(global_arg.delay)
player = None
player = AudioPlayer(play_arg)

if player:
    logger.info("Start playing ...")
    try:
        print("Playback started. Press Ctrl+C to stop.")
        player.begin()
        while True:
            # Endless loop for playback. It will keep playing until KeyboardInterrupt is raised.
            pass
    except KeyboardInterrupt:
        logger.info("Stop playing ...")
        player.end()


