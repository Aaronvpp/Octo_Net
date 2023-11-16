import pickle
import numpy as np
# Specify the pickle file name
pickle_filename = '/home/aiot-mini/code/DeptCam/output_1/depth_image_output_1/depth_image_0001.pkl'

# Open the pickle file and load its contents into a variable
with open(pickle_filename, 'rb') as f:
    depth_image_gray = pickle.load(f)

# Convert the depth_image_gray (numpy array) to a string representation
depth_image_gray_str = np.array2string(depth_image_gray)
# Set the print options for NumPy
np.set_printoptions(threshold=np.inf, linewidth=np.inf)
# Specify the text file name
text_filename = 'depth_image_0002.txt'
# Now print the depth_image_gray matrix
print(depth_image_gray.max())
# Save the depth_image_gray_str to a text file
with open(text_filename, 'w') as f:
    f.write(depth_image_gray_str)