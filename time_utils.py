import ntplib
from datetime import datetime
import socket

def get_ntp_time_and_difference(retries=10):
    for _ in range(retries):
        try:
            ntp_time = get_ntp_time()
            local_time = datetime.now()
            time_difference = ntp_time - local_time
            print("ntp_time", ntp_time, "time_difference", time_difference)
            break
        except ntplib.NTPException:
            print("Failed to get NTP time. Retrying...")
            time_difference = None
    else:
        print("Failed to get NTP time after all retries. Using only local time.")
        ntp_time = datetime.now()

    return ntp_time, time_difference

def get_fake_ntp_time(local_time, time_difference):
    if time_difference:
        fake_ntp_time = local_time + time_difference
    else:
        fake_ntp_time = local_time

    return fake_ntp_time.strftime('%Y-%m-%d %H:%M:%S.%f')

def get_ntp_time(server="192.168.31.35", port=1230):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server, port))
    ntp_time_str = client_socket.recv(1024).decode().strip()
    client_socket.close()

    return datetime.strptime(ntp_time_str, '%Y-%m-%d %H:%M:%S.%f')

if __name__ == "__main__":
    ntp_time = get_ntp_time()
    # print(f"Fake NTP time: {ntp_time}")

