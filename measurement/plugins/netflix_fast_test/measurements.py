import requests
import re
import time
from threading import Thread

from measurement.measurements import BaseMeasurement
from measurement.results import Error
from measurement.units import RatioUnit, TimeUnit, StorageUnit, NetworkUnit


NETFLIX_ERRORS = {

}
CHUNK_SIZE = 100 * 1024
MAX_TIME = 12
SLEEP_SECONDS = 1

total = 0
done = 0

class NetflixFastTest(BaseMeasurement):
    def __init__(self, id, servers=None):
        super(NetflixFastTest, self).__init__(id=id)
        self.id = id
        self.done = 0
        self.total = 0
        self.sessions = []

    def measure(self):
        s = requests.Session()
        token = self.get_token(s)
        urls = self.get_urls(s, token)
        print(urls)
        self.thread_stuff(urls)
        time.sleep(1)
        # conns = self.get_connections(urls)
        # self.threaded_download_other(conns[0])
        # self.measure_connections(conns)


    def get_token(self, s):
        resp = s.get("http://fast.com/")
        text = resp.text
        script = re.search(r'<script src="(.*?)">', text).group(1)
        script_resp = s.get('https://fast.com{script}'.format(script=script))
        script_text = script_resp.text
        token = re.search(r'token:"(.*?)"', script_text).group(1)
        return token

    def get_urls(self, s, token):
        params = {'https': 'true', 'token': token, 'urlCount': 3}
        resp = s.get('https://api.fast.com/netflix/speedtest', params=params)
        data = resp.json()
        return [x['url'] for x in data]

    def get_connections(self, urls):
        conns = [self.get_connection(url) for url in urls]
        return conns

    def get_connection(self, url):
        s = requests.Session()
        self.sessions.append(s)
        conn = s.get(url, stream=True)
        return conn

    def measure_connections(self, conns):
        # This will have to be threaded!
        workers = [self.measure_speed(conn) for conn in conns]

    def thread_stuff(self, urls):
        s = requests.Session()
        threads = [None] * len(urls)
        results = [0] * len(urls)

        # Create threads
        for i in range(len(urls)):
            print(i)
            threads[i] = Thread(target=self.threaded_download, args=(urls[i], results, s, i))
            threads[i].daemon = True
            threads[i].start()

        last_total = 0
        for loop in range(int(MAX_TIME / SLEEP_SECONDS)):
            # print(results)
            total = 0
            for i in range(len(threads)):
                total += results[i]
            delta = total - last_total
            speed_kbytesps = (delta/SLEEP_SECONDS)/1024
            speed_mbitps = (delta/SLEEP_SECONDS)*8/1024/1024
            print(
                "Loop", loop,
                "Total MB", total / (1024 * 1024),
                "Delta MB", delta / (1024 * 1024),
                "Speed kB/s:", speed_kbytesps,
                "Speed Mbit/s", speed_mbitps
            )
            last_total = total

            time.sleep(SLEEP_SECONDS)
        print(results)


    def threaded_download(self, url, results, s, index):
        thread_total = 0
        print("Thread index: {index} booted".format(index=index))
        start = time.time()
        conn = s.get(url, stream=True)

        g = conn.iter_content(chunk_size=CHUNK_SIZE)
        chunk_count = 1
        for chunk in g:
            # print("Just read a chunk")
            # self.total += len(chunk)
            results[index] += len(chunk)
        # print("Total: {total} for Index: {index}".format(total=total, index=index))
        self.done += 1
        print("Finished in: {x} for Index: {index}".format(x=time.time() - start, index=index))
