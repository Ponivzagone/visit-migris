
import requests
import winsound
import time
from datetime import datetime

duration = 1000  # milliseconds
freq = 440  # Hz
time_now = datetime.now()
REQUEST_STRING = 'https://www.migracija.lt/external/tickets/classif/KL45_10/KL02_88/dates?t={}'.format(time_now.ctime())
while True:

        book_times = [
            time_book.strftime('Y-%m-%d %H:%M:%S') for time_book in (
                datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S') for time_str in requests.get(REQUEST_STRING).json()
            ) if (time_book - time_now).days < 7
        ]

        if book_times:
            winsound.Beep(freq, duration)

        time.sleep(60)
