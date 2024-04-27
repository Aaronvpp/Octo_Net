import cv2
import json
import os
from datetime import datetime, timedelta

# def detect_motion(video_path, buffer_time=2.0, sensitivity=500, pre_buffer_time=0.5):

#     """
#     Detects motion in a video and saves the start and end times of movements to a JSON file.

#     Parameters:
#     - video_path: Path to the video file.
#     - buffer_time: Time in seconds to buffer the end of a movement detection.
#     - sensitivity: The minimum area for a contour to be considered motion.

#     Returns:
#     - A JSON file path where movements are saved.
#     """
#     camera = cv2.VideoCapture(video_path)
#     if not camera.isOpened():
#         print('Failed to open video')
#         return

#     pre_frame = None
#     movement_detected = False
#     movements = []
#     last_movement_time = 0

#     while True:
#         grabbed, frame = camera.read()
#         if not grabbed:
#             if movement_detected and (camera.get(cv2.CAP_PROP_POS_MSEC) / 1000.0 - last_movement_time >= buffer_time):
#                 end_time = last_movement_time
#                 movements.append((max(start_time - pre_buffer_time, 0), end_time))
#                 movement_detected = False
#             break

#         gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)

#         if pre_frame is None:
#             pre_frame = gray_frame
#             continue

#         img_delta = cv2.absdiff(pre_frame, gray_frame)
#         thresh = cv2.threshold(img_delta, 25, 255, cv2.THRESH_BINARY)[1]
#         thresh = cv2.dilate(thresh, None, iterations=2)
#         contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

#         current_time = camera.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
#         movement_now = False
#         for c in contours:
#             if cv2.contourArea(c) < sensitivity:
#                 continue
#             movement_now = True
#             last_movement_time = current_time
#             if not movement_detected:
#                 start_time = current_time
#                 movement_detected = True
#             break

#         if movement_detected and not movement_now and (current_time - last_movement_time >= buffer_time):
#             end_time = last_movement_time
#             movements.append((max(start_time - pre_buffer_time, 0), end_time))
#             movement_detected = False

#         pre_frame = gray_frame

#     camera.release()

#     json_path = os.path.splitext(video_path)[0] + '.json'
#     with open(json_path, 'w') as f:
#         json.dump(movements, f, indent=4)

#     return json_path

def detect_motion(video_path, buffer_time=2.0, sensitivity=500, pre_buffer_time=0.5, min_duration=1.5, post_buffer_time=0.5):
    """
    Detects motion in a video and saves the start and end times of movements to a JSON file,
    excluding movements that last less than the specified minimum duration and adding post buffer time after the movement stops.

    Parameters:
    - video_path: Path to the video file.
    - buffer_time: Time in seconds to buffer the end of a movement detection.
    - sensitivity: The minimum area for a contour to be considered motion.
    - pre_buffer_time: Time in seconds to capture before the detected start of the movement.
    - min_duration: Minimum duration in seconds for a movement to be saved.
    - post_buffer_time: Time in seconds to continue recording after the movement has stopped.

    Returns:
    - A JSON file path where movements are saved.
    """
    camera = cv2.VideoCapture(video_path)
    if not camera.isOpened():
        print('Failed to open video')
        return

    pre_frame = None
    movement_detected = False
    movements = []
    last_movement_time = 0

    while True:
        grabbed, frame = camera.read()
        if not grabbed:
            if movement_detected:
                end_time = last_movement_time + post_buffer_time
                adjusted_start_time = max(start_time - pre_buffer_time, 0)
                if (end_time - adjusted_start_time >= min_duration):
                    movements.append((adjusted_start_time, end_time))
                movement_detected = False
            break

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)

        if pre_frame is None:
            pre_frame = gray_frame
            continue

        img_delta = cv2.absdiff(pre_frame, gray_frame)
        thresh = cv2.threshold(img_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        current_time = camera.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        movement_now = False
        for c in contours:
            if cv2.contourArea(c) < sensitivity:
                continue
            movement_now = True
            last_movement_time = current_time
            if not movement_detected:
                start_time = current_time
                movement_detected = True
            break

        if movement_detected and not movement_now:
            if (current_time - last_movement_time >= buffer_time):
                end_time = last_movement_time + post_buffer_time
                adjusted_start_time = max(start_time - pre_buffer_time, 0)
                if (end_time - adjusted_start_time >= min_duration):
                    movements.append((adjusted_start_time, end_time))
                movement_detected = False

        pre_frame = gray_frame

    camera.release()

    json_path = os.path.splitext(video_path)[0] + '.json'
    with open(json_path, 'w') as f:
        json.dump(movements, f, indent=4)

    return json_path

def load_activities(activities_path):
    """
    Load activities from a file, with each line representing an activity.

    Parameters:
    - activities_path: Path to the file containing activities.

    Returns:
    - A list of activities.
    """
    with open(activities_path, 'r') as f:
        activities = [line.strip() for line in f.readlines()]
    return activities

def convert_to_real_timestamps(json_path, timestamp_path, activities_path):
    """
    Converts the motion detection timestamps to real-world timestamps based on a reference timestamp,
    and associates each segment with an activity. If the number of movements doesn't match the number
    of activities, appends 'error' for unmatched movements.

    Parameters:
    - json_path: Path to the JSON file with motion detection timestamps.
    - timestamp_path: Path to the file containing the reference timestamp.
    - activities_path: Path to the file containing activities for each segment.

    Returns:
    - A JSON file path where the converted timestamps and activities are saved.
    """
    # activities = load_activities(activities_path)
    with open(timestamp_path, 'r') as f:
        first_timestamp_str = f.readline().strip()
    first_timestamp_dt = datetime.strptime(first_timestamp_str, '%Y-%m-%d %H:%M:%S.%f')

    with open(json_path, 'r') as f:
        movements = json.load(f)

    # Ensure there is an activity for each movement; fill with 'error' if not
    # while len(activities) < len(movements):
    #     activities.append('error')
    # if len(activities) == len(movements):
    converted_movements = []
    for i, movement in enumerate(movements):
        start_seconds, end_seconds = movement
        start_datetime = first_timestamp_dt + timedelta(seconds=start_seconds)
        end_datetime = first_timestamp_dt + timedelta(seconds=end_seconds)
        # activity = activities[i] if i < len(activities) else 'error'
        
        converted_movements.append({
            "start": start_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            "end": end_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            # "activity": activity
        })
    # else:
    #     converted_movements = []
    #     for i, movement in enumerate(movements):
    #         start_seconds, end_seconds = movement
    #         start_datetime = first_timestamp_dt + timedelta(seconds=start_seconds)
    #         end_datetime = first_timestamp_dt + timedelta(seconds=end_seconds)
            
    #         converted_movements.append({
    #             "start": start_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
    #             "end": end_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
    #             "activity": 'error,please modify on visualize_app'
    #         })
    output_json_path = os.path.splitext(json_path)[0] + '_datetime.json'
    with open(output_json_path, 'w') as f:
        json.dump(converted_movements, f, indent=4)

    return output_json_path

