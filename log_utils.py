import logging
import os
# from save_timestamp_data import *
from time_utils import *


# Custom log formatter
class NtpLogFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ntp_time, self.time_difference = get_ntp_time_and_difference()

    def format(self, record):
        current_local_time = datetime.now()
        fake_ntp_timestamp = get_fake_ntp_time(current_local_time, self.time_difference)
        record.ntp_time = fake_ntp_timestamp
        return super().format(record)


# Setting up the logger
def setup_logger(output_directory, index):
    log_directory = os.path.join(output_directory, 'logs')
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    log_filename = os.path.join(log_directory, 'config_{}.log'.format(index))  # Changed to use format

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_filename)
    file_formatter = NtpLogFormatter('Local Time: %(asctime)s [%(levelname)s] NTP Time: [%(ntp_time)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger

# Setting up the logger
def setup_logger_global(output_directory, index):
    log_directory = os.path.join(output_directory, 'logs')
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    log_filename = os.path.join(log_directory, 'config_{}.log'.format(index))

    # Create a unique logger name using the index
    logger_name = "global_logger_{}".format(index)
    
    # Check if the logger already exists, if so return the existing logger
    if logger_name in logging.root.manager.loggerDict:
        return logging.getLogger(logger_name)

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_filename, mode='a')
    file_formatter = NtpLogFormatter('Local Time: %(asctime)s [%(levelname)s] NTP Time: [%(ntp_time)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger

# Setting up the logger
def setup_logger_global_terminate(output_directory, index):
    log_directory = os.path.join(output_directory, 'logs')
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    log_filename = os.path.join(log_directory, 'config_{}.log'.format(index))

    # Create a unique logger name using the index
    logger_name = "global_logger_{}".format(index)
    
    # Check if the logger already exists, if so return the existing logger
    if logger_name in logging.root.manager.loggerDict:
        return logging.getLogger(logger_name)

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_filename, mode='a')
    file_formatter = NtpLogFormatter('Local Time: %(asctime)s [%(levelname)s] NTP Time: [%(ntp_time)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


# Usage example
if __name__ == '__main__':
    output_directory = os.path.dirname(os.path.abspath(__file__))
    logger = setup_logger(output_directory)
    logger.info('Program started.')
    logger.debug('This is a debug message.')
    logger.warning('This is a warning message.')
    logger.error('This is an error message.')
    logger.info('Program finished.')