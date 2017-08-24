#coding:utf-8

'''
Date:2017.02.09
About:Python实现多线程HTTP文件下载器（Python2.7.x + win/Linux)
Author:Ben
'''

import time
import threading
import urllib2
import urllib
import sys
max_thread = 10
lock = threading.RLock()
data_lock = threading.Lock()

class Downloader(threading.Thread):
    def __init__(self, url, proxy):
        self.url = url
        self.proxy_list = proxy
        self.start = time.time()
        self.speed = [ 0 for n in range(len(self.proxy_list))]
        self.data_pool = []
        self.data_done = 0
        self.filename = ''
        threading.Thread.__init__(self)

    def getFilename(self):
        url = self.url
        protocol, s1 = urllib.splittype(url)
        host, path = urllib.splithost(s1)
        filename = path.split('/')[-1]
        if '.' not in filename:
            filename = None
        self.filename = filename
        return filename

    def getLength(self):
        opener = urllib2.build_opener()
        try:
          req = opener.open(self.url)
          meta = req.info()
          length = int(meta.getheaders("Content-Length")[0])
          return length
        except urllib2.HTTPError, err:
          if err.code == 404:
             print "Resource Not Found!"
             return 0
          else:
             raise

    def get_range(self):
        ranges = []
        length = self.getLength()
        if length == 0:
           return ranges
        offset = 20000000
        if length < offset:
           segment_num = 1
        else:
           segment_num = length/offset

	if segment_num == 1:
           ranges.append((0,length))
           return ranges        
        for i in range(segment_num):
            if i == (segment_num - 1):
                ranges.append((i*offset,length))
            else:
                ranges.append((i*offset,(i+1)*offset))
        return ranges

    def downloadThread(self,data_pool,proxy,n):
        while 1:
          req = urllib2.Request(self.url)
          with data_lock:
             if len(self.data_pool) == 0:
                return
             start, end = self.data_pool[0]
             del self.data_pool[0]
          req.headers['Range'] = 'bytes=%s-%s' % (start, end)
          proxy_handler = urllib2.ProxyHandler({"http": proxy})
          opener = urllib2.build_opener(proxy_handler) 
          f = opener.open(req)
          offset = start
          buffer = 1024
          num = 0
          begin_time = time.time()
          tmp_total = 0
          while 1:
            block = f.read(buffer)
         
            if not block:
                self.speed[n] = 0
                break

            tmp_total += len(block)
            #num += 1 
            #if num >= 300:
            interval_time = time.time() - begin_time
            if interval_time >= 1:
                self.speed[n] = (tmp_total/interval_time/1024/1024)
                #print('thread %d : speed :%.2f elapse time : %f' %(n,float(tmp_total/interval_time/1024/1024),interval_time))
                begin_time = time.time()
                tmp_total = 0
                num = 0           
            with lock:
                self.file.seek(offset)
                self.file.write(block)
                offset = offset + len(block)
                self.data_done += len(block)

    def calculate_total(self):
        return (float(self.data_done)/self.getLength())*100

    def calculate_speed(self):
        total_speed = 0
        for tmp in self.speed:
            #print('tmp speed is %f' %tmp)
            total_speed += tmp
        return total_speed

    def show(self):
        while 1:
            percent = self.calculate_total()
            if int(percent) == 100:
               print('Progress: 100%% . Current speed : %.2f(MB/s)' %(self.calculate_speed()))
               break
            print('Progress: %d%% . Current speed : %.2f(MB/s)' %(percent, self.calculate_speed()))
            time.sleep(3)

    def download(self):
        filename = self.getFilename()
        self.data_pool = self.get_range()
        if len(self.data_pool) == 0:
           print 'No data to download! Please check your URL!'
           exit(1)
        self.file = open(filename, 'wb')
        thread_list = []
        n = 0
        for proxy in self.proxy_list:
            #print 'starting:%d thread '% n
            thread = threading.Thread(target=self.downloadThread,args=(self.data_pool,proxy,n))
            thread.start()
            thread_list.append(thread)
            n += 1

        thread_show = threading.Thread(target=self.show)
        thread_show.start()
        thread_list.append(thread_show)
        for i in thread_list:
            i.join()
        print 'Download %s Success!'%(self.filename)
        self.file.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
       print 'Usage: download.exe source_url'
       sys.exit()
    if len(sys.argv) > 2:
       print 'Only Download the first one : sys.argv[1]'
    url = sys.argv[1]
    #url = "http://bd.cstor.cn:6666/test.mp4"
    #url = "http://bd.cstor.cn:6666/log.txt"
    #url = "http://mirrors.163.com/centos/7/isos/x86_64/CentOS-7-x86_64-Minimal-1611.iso"
    start = time.time()
    proxy_list = ['http://192.168.10.93:8888', 'http://192.168.10.94:8888', 'http://192.168.10.57:8888', 'http://192.168.10.61:8888', 'http://192.168.10.56:8888', 'http://192.168.10.102:8888'] 
    down = Downloader(url,proxy_list)
    down.download()
    end = time.time()
    print('Total Download Time: %.2fs' % (end-start))
    print('Average Download Speed: %.2fMB/s' % (down.getLength()/1024/1024/(end-start)))
