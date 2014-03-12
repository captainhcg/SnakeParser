import urllib
import urlparse
import settings
import Queue
import threading
from pymongo import MongoClient

from bs4 import BeautifulSoup, UnicodeDammit

class SnakeParser(object):
    def __init__(self):
        self.start_url = settings.START_URL
        self.scope = settings.SCOPE
        self.parsed = set()
        self.lock = threading.Lock()
        self.num_threads = settings.NUM_THREADS
        self.queue = Queue.Queue()
        self.client = MongoClient(settings.DB_HOST, settings.DB_PORT)
        self.db = self.client[settings.DB_NAME]
        self.pages = self.db['Page']

    def fetchAll(self):
        self.firstFetch()
        thread_list = []
        for _ in xrange(self.num_threads):
            thread_list.append(threading.Thread(target=self.fetch))
        for t in thread_list:
            t.start()
        for t in thread_list:
            t.join()
        print "done" 

    def firstFetch(self):
        self.process_url(self.start_url, "")

    def process_page(self, url, parent, html_text):
        page = self.pages.find_one({"url": url}) or {"url": url}
        page["parent"] = parent
        page["html"] = UnicodeDammit(html_text).unicode_markup
        self.pages.save(page)
        print url, parent

    def process_url(self, url, parent):
        # print url, threading.current_thread()
        try:
            response = urllib.urlopen(url)
        except Exception as e:
            print "%s: %s"%(Exception, e)
            return
        html_text = response.read()
        self.process_page(url, parent, html_text)
        soup = BeautifulSoup(html_text)
        for link in soup.find_all('a', href=True):
            new_url = urlparse.urljoin(url, link['href'])
            if new_url.startswith(self.scope):
                self.lock.acquire()
                if new_url not in self.parsed:
                    self.queue.put([new_url, url])
                    self.parsed.add(new_url)
                self.lock.release()        

    def fetch(self):
        while not self.queue.empty():
            self.lock.acquire()
            if self.queue.empty():
                continue
            url, parent = self.queue.get()
            self.lock.release()
            self.process_url(url, parent)

if __name__ == "__main__":
    parser = SnakeParser()
    parser.fetchAll()
