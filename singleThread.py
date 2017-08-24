#coding:utf-8

#实现单线程下载
from analysisUrl import url, filename
from conWebServer import s
from httpPacket import packet
import re
import time

class downloader:
    def __init__(self):
        self.url = url
        self.filename = filename

    def getLength(self):
        s.send(packet)
        print "send success!"
        buf = s.recv(1024)
        p = re.compile(r'Content-Length: (\d*)')
        length = int(p.findall(buf)[0])
        return length, buf

    def download(self):
        file = open(self.filename,'wb')
        length,buf = self.getLength()
        packetIndex = buf.index('\r\n\r\n')
        buf = buf[packetIndex+4:]
        file.write(buf)
        sum = len(buf)
        while 1:
            buf = s.recv(1024)
            file.write(buf)
            sum = sum + len(buf)
            if sum >= length:
                break
        print "Success!!"

if __name__ == "__main__":
    start = time.time()
    down = downloader()
    down.download()
    end = time.time()
    print "The time spent on this program is %f s"%(end - start)

