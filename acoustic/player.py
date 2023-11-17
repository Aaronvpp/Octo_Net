from config import play_arg, process_arg, global_arg
from acoustic.audio.audio import AudioPlayer, AudioPlayandRecord
from time import sleep
from loguru import logger

logger.info("Delay {}s".format(global_arg.delay))
sleep(global_arg.delay)
player = None
player = AudioPlayer(play_arg)

if player:
    logger.info("Start playing ...")
    try:
        while True:
            player.begin()
    except KeyboardInterrupt:
        logger.info("Stop playing ...")
        data_record = player.get_record()
        if global_arg.set_save:
            player.save_record()
        # player.end()
        player.end()


