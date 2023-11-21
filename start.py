import subprocess
import os

# List of Python programs to run
programs = [
    'Audio_Collector/main.py',
    'TermalSensor/termal.py',
    # Add more programs here
]

# Arguments for the programs
arguments = [
    ["json", "Audio_Collector/config_file/speed_playfromfile_new.json"],
    [],
    # [] for programs without arguments,
    # Add more arguments here
]

# Function to run a program
def run_program(program, args):
    return subprocess.Popen(['python', program, *args])

# Create a list to store the subprocesses
processes = []



# Start running the programs
for i, program in enumerate(programs):
    process = run_program(program, arguments[i])
    processes.append(process)

# Wait for all processes to finish
for process in processes:
    process.wait()