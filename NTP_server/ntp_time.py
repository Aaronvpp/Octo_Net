import socket
from datetime import datetime
import pytz
def get_ntp_time():
    utc_time = datetime.now(pytz.utc)
    japan_timezone = pytz.timezone('Asia/Hong_Kong')
    ntp_time = utc_time.astimezone(japan_timezone)
    return ntp_time

def start_ntp_time_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(1)
    # print(f"[*] NTP Time Server started on {host}:{port}")

    while True:
        client_socket, client_address = server_socket.accept()
        # print(f"[*] Connection from {client_address}")

        ntp_time = get_ntp_time()
        ntp_time_str = ntp_time.strftime('%Y-%m-%d %H:%M:%S.%f') + '\n'
        client_socket.sendall(ntp_time_str.encode())
        
        client_socket.close()

if __name__ == "__main__":
    host = "192.168.31.35" #modify this and time_utils.py and mqtt_listener.py and mqtt.py when you change the network
    port = 1230
    start_ntp_time_server(host, port)