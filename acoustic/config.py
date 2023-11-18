from argparse import ArgumentParser
import os
from loguru import logger
import parser_config
from parser_config import GlobalArgs, PlayArgs, ProcessArgs, DeviceArgs
from index_manager import IndexManager, index_config
from check_param import set_and_check_param
from loguru import logger
import parser_config
import anyconfig as ac

# >>>>>>>>>>>>>>>>>>>>>>>>>>>> Parser Configuration  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
arg_parser = ArgumentParser()
arg_subparser = arg_parser.add_subparsers(dest='command')

logger.info("Parsing arguments...")
arg_config_parser = arg_subparser.add_parser('config',
                                             description='Manual configuration')
parser_config.set_play_args_arguments(arg_config_parser)
parser_config.set_global_args_arguments(arg_config_parser)
parser_config.set_process_args_arguments(arg_config_parser)
parser_config.set_device_args_arguments(arg_config_parser)

arg_json_parser = arg_subparser.add_parser('json',
                                           description='Json configuration')
parser_config.set_json_args_arguments(arg_json_parser)


arg_gui_parser = arg_subparser.add_parser('gui',
                                          description='GUI configuration')


args = arg_parser.parse_args()
args_dict = vars(args)

play_arg:PlayArgs = PlayArgs()
global_arg:GlobalArgs = GlobalArgs()
device_arg:PlayArgs = PlayArgs()
process_arg:ProcessArgs = ProcessArgs()


# priority: dataplay_name > json > config > default
if args.command == 'config':
    parser_config.parse_parser_args(args_dict,
                                    play_arg=play_arg,
                                    process_arg=process_arg,
                                    device_arg=device_arg,
                                    global_arg=global_arg)

elif args.command == 'json':
    with open(args.json_file, 'r') as json_file:
        parser_config.parse_json_file(json_file,
                                      play_arg=play_arg,
                                      process_arg=process_arg,
                                      device_arg=device_arg,
                                      global_arg=global_arg)
elif args.command == 'gui':
    # import subprocess
    # subprocess.run("streamlit run app.py", shell=True)
    raise NotImplementedError("GUI is not implemented yet, please run app.py")
else:
    raise ValueError("Unknown command: {}".format(args.command))

print(play_arg.__dict__)
if play_arg.load_dataplay:
    try:
        play_arg.play_path = os.path.join(
            play_arg.dataplay_path, play_arg.dataplay_name)
        logger.info("Load dataplay from: {}".format(play_arg.play_path))
    finally:
        parser_config.parse_dataplay_param(play_arg.dataplay_name, play_arg)


# >>>>>>>>>>>>>>>>>>>>>>>>>>>> Index Configuration  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# index_manager = IndexManager(global_arg=global_arg,
#                              play_arg=play_arg,
#                              device_arg=device_arg)
# data_name, rec_idx = index_manager()


# global_arg.rec_idx = rec_idx if not hasattr(global_arg, "rec_idx") \
#     else global_arg.rec_idx

# global_arg.data_name = data_name
# global_arg.data_folder = os.path.join(
#     global_arg.save_root, global_arg.data_name)
# if not os.path.exists(global_arg.data_folder):
#     os.mkdir(os.path.join(global_arg.data_folder))
# global_arg.data_path = os.path.join(
#     global_arg.data_folder, global_arg.data_name)

global_arg, data_name, rec_idx = index_config(global_arg=global_arg,
                                              play_arg=play_arg,
                                              device_arg=device_arg)
logger.info("Data name: {}".format(data_name))
logger.info("idx: {}".format(rec_idx))


# >>>>>>>>>>>>>>>>>>>>>>>>>>>> Check Parameters  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
set_and_check_param(play_arg=play_arg,
                    global_arg=global_arg,
                    process_arg=process_arg,
                    device_arg=device_arg)


# >>>>>>>>>>>>>>>>>>>>>>>>>>> Logger Configuration  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
global_arg.log_path = global_arg.data_path + ".log"
logger.add(global_arg.log_path)

# >>>>>>>>>>>>>>>>>>>>>>>>>>> Print Parameters  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
param_dict = {
    "play_arg": play_arg.__dict__,
    "global_arg": global_arg.__dict__,
    "process_arg": process_arg.__dict__,
    "device_arg": device_arg.__dict__
}


# add all parameters to logger
for param_name, param in param_dict.items():
    logger.info("Printing {} ...".format(param_name))
    for key, value in param.items():
        logger.info("{}: {}".format(key, value))

# save all parameters to json
with open(global_arg.data_path + "_params.json", "w") as f:
    ac.dump(param_dict, f)



