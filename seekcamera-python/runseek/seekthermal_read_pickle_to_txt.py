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

    with open(pickle_file, 'rb') as f:
        data_dicts = pickle.load(f)
    print(data_dicts)
    with open(output_txt_file, 'w') as f:
        for index, data_dict in enumerate(data_dicts):
            f.write(f"Data {index}:\n")
            f.write(f"Timestamp: {data_dict['timestamp']}\n")
            f.write("Temperature data:\n")
            for row in data_dict['data']:
                row_str = ' '.join([f"{item:.5f}" for item in row])
                f.write(f"{row_str}\n")
            f.write("\n")

# import os
# import glob
# import pickle

# # Create the directory if it doesn't exist
# output_directory = "txt_reader"
# if not os.path.exists(output_directory):
#     os.makedirs(output_directory)

# pickle_files = glob.glob("output_*.pickle")

# for pickle_file in pickle_files:
#     output_txt_file = pickle_file.replace(".pickle", ".txt")
#     output_txt_file = os.path.join(output_directory, output_txt_file)

#     with open(pickle_file, 'rb') as f:
#         data_dict = pickle.load(f)

#     timestamp = data_dict['timestamp']
#     depth_image = data_dict['data']

#     with open(output_txt_file, 'w') as f:
#         f.write(f"Timestamp: {timestamp}\n")
#         f.write("data:\n")
#         for row in depth_image:
#             row_str = ' '.join([str(x) for x in row])
#             f.write(row_str + "\n")
#         f.write("\n")
# Create the directory if it doesn't exist

# import os
# import glob
# import pickle

# pickle_files = glob.glob("output_*.pickle")
# def load_data_from_pickle(file_path):
#     data_list = []
#     with open(file_path, 'rb') as file:
#         while True:
#             try:
#                 data_list.append(pickle.load(file))
#             except EOFError:
#                 break
#     return data_list

# # Replace 'path/to/your/pickle/file.pickle' with the actual path to your pickle file
# data_list = load_data_from_pickle(pickle_files)

# for data_item in data_list:
#     print(f"Timestamp: {data_item['timestamp']}")
#     print(f"Temperature data: {data_item['data']}")