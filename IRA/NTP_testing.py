import os 
import time 
import ntplib 
 
 


def get_time():
    c = ntplib.NTPClient()
    response = c.request('pool.ntp.org')
    ts = response.tx_time
    current_date = time.strftime('%Y-%m-%d', time.localtime(ts))
    current_time = time.strftime('%X', time.localtime(ts))
    return current_date, current_time