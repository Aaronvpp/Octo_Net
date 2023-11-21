bash
#!/bin/bash

python IRA/IRA.py &
python DeptCam/deptcam.py &
python AWR1843-Read-Data-Python-MMWAVE-SDK-3--master/readData_AWR1843.py &
python Audio_Collector/main.py json "/home/aiot-mini/code/Audio_Collector/config_file/speed_playfromfile_new.json"&
python seekcamera-python/runseek/seekcamera-opencv.py &
python polar/H10/connect_H10.py
wait# Wait for all background processes to finish