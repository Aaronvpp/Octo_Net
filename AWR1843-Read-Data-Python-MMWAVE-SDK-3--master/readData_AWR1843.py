import serial
import time
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtWidgets
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from PyQt5 import QtGui
import pyqtgraph.opengl as gl
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from time_utils import *
from save_timestamp_data import *
from log_utils import *
from sampling_rate import SamplingRateCalculator
import configparser
import json
import pickle
import math


def close(self):
    """End connection between radar and machine

    Returns:
        None

    """
    self.cli_port.write('sensorStop\n'.encode())
    self.cli_port.close()
    self.data_port.close()
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
    if os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '../terminate_flag.txt'))) or os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), '../terminate_mmwave_flag.txt'))):
        # os.remove("terminate_flag.txt")
        return True
    return False

# Calculate the actual sampling rate
sampler = SamplingRateCalculator("MMWave")
# Initialize the frame to calculate the total frame
frame_counter = 0
# Initial config.ini
config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join(os.path.dirname(__file__), '../config.ini')))
mmwave_settings_str = config.get('device_settings', 'mmwave')
mmwave_settings = json.loads(mmwave_settings_str)

# Change the configuration file name
script_dir = os.path.dirname(os.path.realpath(__file__))
output_directory = script_dir
current_index = get_next_index(output_directory)
# Log 
logger = setup_logger(output_directory, current_index)
config_data = {}
for section in config.sections():
    if section != 'device_settings':
        config_data[section] = dict(config.items(section))
logger.info(f"Loaded configuration: {config_data}")
logger.info(f"Loaded mmwave configuration: {mmwave_settings}")
# configFileName = os.path.join(script_dir, 'profile.cfg')
configFileName = os.path.join(script_dir, 'xwr18xx_profile_2023_09_18T12_35_18_517.cfg')
CLIport = {}
Dataport = {}
byteBuffer = np.zeros(2**20,dtype = 'uint8')
byteBufferLength = 0

# def save_frame_data(index, frame_data, timestamp, subindex, output_directory):
#     data_folder = os.path.join(output_directory, "data")
#     # timestamp_folder = os.path.join(output_directory, "timestamp")

#     if not os.path.exists(data_folder):
#         os.makedirs(data_folder)

#     # if not os.path.exists(timestamp_folder):
#     #     os.makedirs(timestamp_folder)

#     with open(os.path.join(data_folder, f'output_{subindex}.txt'), 'a') as f:
#         f.write(f"NTP_Server_timestamp, {fake_ntp_timestamp} | Framedata: {frame_data}\n")

    # with open(os.path.join(timestamp_folder, f'timestamp_{subindex}.txt'), 'a') as f:
    #     f.write(f"Timestamp: {timestamp}\n")


# ------------------------------------------------------------------

# Function to configure the serial ports and send the data from
# the configuration file to the radar
def serialConfig(configFileName):
    
    global CLIport
    global Dataport
    # Open the serial ports for the configuration and the data ports
    
    # Raspberry pi
    #CLIport = serial.Serial('/dev/ttyACM0', 115200)
    #Dataport = serial.Serial('/dev/ttyACM1', 921600)
    
    # Windows
    CLIport = serial.Serial('/dev/ttyACM0', 115200)
    Dataport = serial.Serial('/dev/ttyACM1', 921600)

    # Read the configuration file and send it to the board
    config = [line.rstrip('\r\n') for line in open(configFileName)]
    for i in config:
        CLIport.write((i+'\n').encode())
        print(i)
        time.sleep(0.01)
        
    return CLIport, Dataport

# ------------------------------------------------------------------

# Function to parse the data inside the configuration file
def parseConfigFile(configFileName):
    configParameters = {} # Initialize an empty dictionary to store the configuration parameters
    
    # Read the configuration file and send it to the board
    config = [line.rstrip('\r\n') for line in open(configFileName)]
    for i in config:
        
        # Split the line
        splitWords = i.split(" ")
        
        # Hard code the number of antennas, change if other configuration is used
        numRxAnt = 4
        numTxAnt = 3
        
        # Get the information about the profile configuration
        if "profileCfg" in splitWords[0]:
            print(splitWords[0],"splitWords[0]")
            startFreq = int(float(splitWords[2]))
            idleTime = int(splitWords[3])
            rampEndTime = float(splitWords[5])
            freqSlopeConst = float(splitWords[8])
            numAdcSamples = int(splitWords[10])
            numAdcSamplesRoundTo2 = 1;
            
            while numAdcSamples > numAdcSamplesRoundTo2:
                numAdcSamplesRoundTo2 = numAdcSamplesRoundTo2 * 2;
                
            digOutSampleRate = int(splitWords[11]);
            
        # Get the information about the frame configuration    
        elif "frameCfg" in splitWords[0]:
            
            chirpStartIdx = int(splitWords[1]);
            chirpEndIdx = int(splitWords[2]);
            numLoops = int(splitWords[3]);
            numFrames = int(splitWords[4]);
            framePeriodicity = float(splitWords[5]);

            
    # Combine the read data to obtain the configuration parameters           
    numChirpsPerFrame = (chirpEndIdx - chirpStartIdx + 1) * numLoops
    configParameters["numDopplerBins"] = numChirpsPerFrame / numTxAnt
    configParameters["numRangeBins"] = numAdcSamplesRoundTo2
    configParameters["rangeResolutionMeters"] = (3e8 * digOutSampleRate * 1e3) / (2 * freqSlopeConst * 1e12 * numAdcSamples)
    configParameters["rangeIdxToMeters"] = (3e8 * digOutSampleRate * 1e3) / (2 * freqSlopeConst * 1e12 * configParameters["numRangeBins"])
    configParameters["dopplerResolutionMps"] = 3e8 / (2 * startFreq * 1e9 * (idleTime + rampEndTime) * 1e-6 * configParameters["numDopplerBins"] * numTxAnt)
    configParameters["maxRange"] = (300 * 0.9 * digOutSampleRate)/(2 * freqSlopeConst * 1e3)
    configParameters["maxVelocity"] = 3e8 / (4 * startFreq * 1e9 * (idleTime + rampEndTime) * 1e-6 * numTxAnt)
    
    return configParameters
   
# ------------------------------------------------------------------

# Funtion to read and parse the incoming data
def readAndParseData18xx(Dataport, configParameters):
    global byteBuffer, byteBufferLength
    
    # Constants
    OBJ_STRUCT_SIZE_BYTES = 12;
    BYTE_VEC_ACC_MAX_SIZE = 2**15;
    MMWDEMO_UART_MSG_DETECTED_POINTS = 1;
    MMWDEMO_UART_MSG_RANGE_PROFILE   = 2;
    maxBufferSize = 2**15;
    tlvHeaderLengthInBytes = 8;
    pointLengthInBytes = 16;
    magicWord = [2, 1, 4, 3, 6, 5, 8, 7]
    
    # Initialize variables
    magicOK = 0 # Checks if magic number has been read
    dataOK = 0 # Checks if the data has been read correctly
    frameNumber = 0
    detObj = {}
    
    readBuffer = Dataport.read(Dataport.in_waiting)
    byteVec = np.frombuffer(readBuffer, dtype = 'uint8')
    byteCount = len(byteVec)
    
    # Check that the buffer is not full, and then add the data to the buffer
    if (byteBufferLength + byteCount) < maxBufferSize:
        byteBuffer[byteBufferLength:byteBufferLength + byteCount] = byteVec[:byteCount]
        byteBufferLength = byteBufferLength + byteCount
        
    # Check that the buffer has some data
    if byteBufferLength > 16:
        
        # Check for all possible locations of the magic word
        possibleLocs = np.where(byteBuffer == magicWord[0])[0]

        # Confirm that is the beginning of the magic word and store the index in startIdx
        startIdx = []
        for loc in possibleLocs:
            check = byteBuffer[loc:loc+8]
            if np.all(check == magicWord):
                startIdx.append(loc)
               
        # Check that startIdx is not empty
        if startIdx:
            
            # Remove the data before the first start index
            if startIdx[0] > 0 and startIdx[0] < byteBufferLength:
                byteBuffer[:byteBufferLength-startIdx[0]] = byteBuffer[startIdx[0]:byteBufferLength]
                byteBuffer[byteBufferLength-startIdx[0]:] = np.zeros(len(byteBuffer[byteBufferLength-startIdx[0]:]),dtype = 'uint8')
                byteBufferLength = byteBufferLength - startIdx[0]
                
            # Check that there have no errors with the byte buffer length
            if byteBufferLength < 0:
                byteBufferLength = 0
                
            # word array to convert 4 bytes to a 32 bit number
            word = [1, 2**8, 2**16, 2**24]
            
            # Read the total packet length
            totalPacketLen = np.matmul(byteBuffer[12:12+4],word)
            
            # Check that all the packet has been read
            if (byteBufferLength >= totalPacketLen) and (byteBufferLength != 0):
                magicOK = 1
    
    # If magicOK is equal to 1 then process the message
    if magicOK:
        # word array to convert 4 bytes to a 32 bit number
        word = [1, 2**8, 2**16, 2**24]
        
        # Initialize the pointer index
        idX = 0
        
        # Read the header
        magicNumber = byteBuffer[idX:idX+8]
        idX += 8
        version = format(np.matmul(byteBuffer[idX:idX+4],word),'x')
        idX += 4
        totalPacketLen = np.matmul(byteBuffer[idX:idX+4],word)
        idX += 4
        platform = format(np.matmul(byteBuffer[idX:idX+4],word),'x')
        idX += 4
        frameNumber = np.matmul(byteBuffer[idX:idX+4],word)
        idX += 4
        timeCpuCycles = np.matmul(byteBuffer[idX:idX+4],word)
        idX += 4
        numDetectedObj = np.matmul(byteBuffer[idX:idX+4],word)
        idX += 4
        numTLVs = np.matmul(byteBuffer[idX:idX+4],word)
        idX += 4
        subFrameNumber = np.matmul(byteBuffer[idX:idX+4],word)
        idX += 4

        # Read the TLV messages
        for tlvIdx in range(numTLVs):
            
            # word array to convert 4 bytes to a 32 bit number
            word = [1, 2**8, 2**16, 2**24]

            # Check the header of the TLV message
            tlv_type = np.matmul(byteBuffer[idX:idX+4],word)
            idX += 4
            tlv_length = np.matmul(byteBuffer[idX:idX+4],word)
            idX += 4

            # Read the data depending on the TLV message
            if tlv_type == MMWDEMO_UART_MSG_DETECTED_POINTS:

                # Initialize the arrays
                x = np.zeros(numDetectedObj,dtype=np.float32)
                y = np.zeros(numDetectedObj,dtype=np.float32)
                z = np.zeros(numDetectedObj,dtype=np.float32)
                velocity = np.zeros(numDetectedObj,dtype=np.float32)
                
                for objectNum in range(numDetectedObj):
                    
                    # Read the data for each object
                    x[objectNum] = byteBuffer[idX:idX + 4].view(dtype=np.float32)
                    idX += 4
                    y[objectNum] = byteBuffer[idX:idX + 4].view(dtype=np.float32)
                    idX += 4
                    z[objectNum] = byteBuffer[idX:idX + 4].view(dtype=np.float32)
                    idX += 4
                    velocity[objectNum] = byteBuffer[idX:idX + 4].view(dtype=np.float32)
                    idX += 4
                
                # Store the data in the detObj dictionary
                detObj = {"numObj": numDetectedObj, "x": x, "y": y, "z": z, "velocity":velocity}
                dataOK = 1
                
 
        # Remove already processed data
        if idX > 0 and byteBufferLength>idX:
            shiftSize = totalPacketLen
            
                
            byteBuffer[:byteBufferLength - shiftSize] = byteBuffer[shiftSize:byteBufferLength]
            byteBuffer[byteBufferLength - shiftSize:] = np.zeros(len(byteBuffer[byteBufferLength - shiftSize:]),dtype = 'uint8')
            byteBufferLength = byteBufferLength - shiftSize
            
            # Check that there are no errors with the buffer length
            if byteBufferLength < 0:
                byteBufferLength = 0         

    return dataOK, frameNumber, detObj

# ------------------------------------------------------------------

# scatter_plot_collection = ax.scatter([], [], [], c='r', marker='o')

# Funtion to update the data and display in the plot
def update():
     
    dataOk = 0
    global detObj
    global scatter_plot_collection 
    x = []
    y = []
      
    # Read and parse the received data
    dataOk, frameNumber, detObj = readAndParseData18xx(Dataport, configParameters)
    
    if dataOk and len(detObj["x"])>0:
        #print(detObj)
        x = -detObj["x"]
        y = detObj["y"]
        
        # s.setData(x,y)
        # QtWidgets.QApplication.processEvents()
        # scatter_plot.setData(pos=np.column_stack((x, y, detObj["z"])), color=(1, 0, 0, 1), size=0.1, pxMode=True)
        # scatter_plot_collection.remove()
        if scatter_plot_collection:  # Check if scatter_plot_collection has any data
            scatter_plot_collection.remove()  # Remove the existing data

        scatter_plot_collection = ax.scatter(x, y, detObj["z"], c='r', marker='o')
        #uncomment if you want to plot
        plt.draw()
        plt.pause(0.1)
        #QtGui.QApplication.processEvents()
        QtWidgets.QApplication.processEvents()
    
    return dataOk


# -------------------------    MAIN   -----------------------------------------  

# Configurate the serial port
CLIport, Dataport = serialConfig(configFileName)

# Get the configuration parameters from the configuration file
configParameters = parseConfigFile(configFileName)

# START QtAPPfor the plot
# app = QtGui.QApplication([])
# app = QtWidgets.QApplication([])
# Set the plot 
# pg.setConfigOption('background','w')
# win = pg.GraphicsLayoutWidget(title="2D scatter plot")
# p = win.addPlot()
# p.setXRange(-0.5,0.5)
# p.setYRange(0,1.5)
# p.setLabel('left',text = 'Y position (m)')
# p.setLabel('bottom', text= 'X position (m)')
# s = p.plot([],[],pen=None,symbol='o')

# win = QtWidgets.QMainWindow()
# win.setWindowTitle('3D Scatter plot')
# gl_widget = gl.GLViewWidget()
# win.setCentralWidget(gl_widget)

# gl_widget.opts['distance'] = 50
# gl_widget.show()

# scatter_plot = gl.GLScatterPlotItem()

# gl_widget.addItem(scatter_plot)

# # Set axes labels
# axis = gl.GLAxisItem()
# axis.setSize(2, 2, 2)
# gl_widget.addItem(axis)
# win.show()
# Create a 3D scatter plot
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.set_xlabel('X position (m)')
ax.set_ylabel('Y position (m)')
ax.set_zlabel('Z position (m)')
# Set the axis limits
ax.set_xlim(-5, 5)
ax.set_ylim(0, 3)
ax.set_zlim(-5, 5)
scatter_plot_collection = ax.scatter([], [], [], c='r', marker='o')  # Create an empty scatter plot collection
   
# Main loop 
detObj = {}  
frameData = {}    
currentIndex = 0
timeflag = True
# subindex = 0
# data_filename = os.path.join(output_directory, "data", f'output_{subindex}.pickle')

# while os.path.exists(data_filename):
#         subindex += 1
#         data_filename = os.path.join(output_directory, "data", f'output_{subindex}.pickle')
data_folder = os.path.join(output_directory, "data")

if not os.path.exists(data_folder):
    os.makedirs(data_folder)

file_path = os.path.join(data_folder, f'output_{current_index}.pickle')
with open(file_path, 'ab') as f:
    while True:
        try:
            # win.show()
            # Update the data and check if the data is okay
            dataOk = update()
            
            if dataOk:
                # Store the current frame into frameData
                frameData[currentIndex] = detObj
                currentIndex += 1
                # print("frameData",frameData)
                
                # if not os.path.exists(output_{subindex}.txt):
                #     subindex += 1
                # Save frame data and timestamp
                if timeflag:
                    ntp_time, time_difference = get_ntp_time_and_difference()
                    fake_ntp_timestamp = ntp_time
                    logger.info("Using NTP time as the start timmer.")
                    timeflag = False
                else:
                    current_local_time = datetime.now()
                    fake_ntp_timestamp = get_fake_ntp_time(current_local_time, time_difference)
                    logger.info("Using the local timmer to pretend to be NTP time. Data recorded")
                # Save frame data and timestamp
                print("NTP_Server_timestamp", fake_ntp_timestamp)
                save_timestamp_data_modified(detObj, fake_ntp_timestamp, f)
                # To calculate the actual sampling rate
                sampler.update_loop()
                # Calculate the total frame
                frame_counter += 1
            
            time.sleep(0.001) # Sampling frequency of 30 Hz
            if check_terminate_flag():
                CLIport.write(('sensorStop\n').encode())
                CLIport.close()
                Dataport.close()
                logger.info("End recording by a terminate action.")
                pickle_size = os.path.getsize(file_path)
                human_readable_size = convert_size(pickle_size)
                with open(os.path.join(os.path.dirname(__file__), "mmwave_data_saved_status.txt"), "w") as f:
                        f.write(f"mmwave Data saved /AWR1843-Read-Data-Python-MMWAVE-SDK-3--master/data/output_{current_index}.pickle,\n")
                        f.write(f"mmwave Log saved /AWR1843-Read-Data-Python-MMWAVE-SDK-3--master/logs/config_{current_index}.log\n")
                        f.write(f"Total frames processed: {frame_counter},\n")
                        f.write(f"Pickle file size: {human_readable_size}\n")
                break
                
            
        # Stop the program and close everything if Ctrl + c is pressed
        except KeyboardInterrupt:
            CLIport.write(('sensorStop\n').encode())
            CLIport.close()
            Dataport.close()
            # win.close()
            plt.close()
            break
        
    





