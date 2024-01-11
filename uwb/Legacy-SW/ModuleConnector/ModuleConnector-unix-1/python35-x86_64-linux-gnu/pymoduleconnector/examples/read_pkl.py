import pickle
import glob
import os

def read_from_pickle(pickle_file):
    """Reads data from a pickle file."""
    data = []
    with open(pickle_file, 'rb') as f:
        while True:
            try:
                data.append(pickle.load(f))
            except EOFError:
                break
    return data

def write_to_text(data, text_file):
    """Writes data to a text file."""
    with open(text_file, 'w') as f:
        for item in data:
            timestamp = item["timestamp"]
            frame = item["frame"]
            f.write("Timestamp: {}, Frame: {}\n".format(timestamp, frame))

def main():
    output_directory = "txt_reader"
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    # Find all pickle files
    for pickle_file in glob.glob('output_*.pickle'):
        # Read data from pickle
        data = read_from_pickle(pickle_file)

        # Generate text file path
        text_file = os.path.join(output_directory, os.path.splitext(os.path.basename(pickle_file))[0] + '.txt')

        # Write data to text file
        write_to_text(data, text_file)

        print("Data from {} has been written to {}".format(pickle_file, text_file))

if __name__ == '__main__':
    main()
