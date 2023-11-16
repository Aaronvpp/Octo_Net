# import os
# import glob
# import pickle

# # Create the directory if it doesn't exist
# output_directory = "txt_reader"
# if not os.path.exists(output_directory):
#     os.makedirs(output_directory)

# pickle_files = glob.glob("depth_image_*.pkl")

# for pickle_file in pickle_files:
#     output_txt_file = pickle_file.replace(".pkl", ".txt")
#     output_txt_file = os.path.join(output_directory, output_txt_file)

#     with open(pickle_file, 'rb') as f:
#         data_dict = pickle.load(f)

#     timestamp = data_dict['timestamp']
#     depth_image = data_dict['depth_image']

#     with open(output_txt_file, 'w') as f:
#         f.write(f"Timestamp: {timestamp}\n")
#         f.write("Depth image data:\n")
#         for row in depth_image:
#             row_str = ' '.join([str(x) for x in row])
#             f.write(row_str + "\n")
#         f.write("\n")

import os
import glob
import pickle

# Create the directory if it doesn't exist
output_directory = "txt_reader"
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

pickle_files = glob.glob("output_*.pickle")

for pickle_file in pickle_files:
    output_txt_file = pickle_file.replace(".pickle", ".txt")
    output_txt_file = os.path.join(output_directory, output_txt_file)
    data = []
    with open(pickle_file, 'rb') as f:
        while True:
            try:
                entry = pickle.load(f)
                data.append(entry)
            except EOFError:
                break

    print(data)
    with open(output_txt_file, 'w') as f:
        for entry in data:
            timestamp = entry["timestamp"]
            temp_data = entry["data"]
            f.write(f"Timestamp: {timestamp}\n")
            f.write("Depth_image Data:\n")
            for row in temp_data:
                row_str = " ".join(str(x) for x in row)
                f.write(row_str + "\n")
            f.write("\n")