import Pyro4
import hashlib
import sys
import math as m

from BitTorrent_app.Logic.settings import SIZE

# SPECIAL_DHT_KEYS
maxclient = "#maxclient"
allfiles = "#allfiles"
idclient = "#idclient"
sizefile = "#sizef"
filestep = "#step"    #files in a particular step
maxstep = "#maxstep"  #max step created
lenstep = 50     #cant files in each step

# SPECIAL CONSTANTS
backlog = 50
bufsize = 1024
totalP = 20  # the max number of pieces
histsize = 20
maxpage = 5


class Pagin(object):
    def __init__(self):
        self.files = []
        self.actual_page = 1
        self.pages = {}

    def build(self, files, substring = ""):
        files = [f for f in files if f.find(substring) != -1]
        count = len(files)
        step = m.floor(count/maxpage)

        if step == 0:
            for i in range(1,count + 1):
                print(files[i-1])
                self.pages[i] = files[i-1]
        else:
            for page in range(0,maxpage ):
                if page + 1 == maxpage:
                    self.pages[maxpage] = files[page*step:]
                else:
                    self.pages[page + 1] = files[page*step: page*step + step]


    def inc_actual_page(self):
        if self.actual_page < maxpage:
            self.actual_page += 1

    def dec_actual_page(self):
        if self.actual_page > 1:
            self.actual_page -= 1



def get_remote_node(ip, port):
    uri = "PYRO:" + ip + ":" + str(port) + "@" + ip + ":" + str(port)
    p = Pyro4.Proxy(uri)
    return p


def start_service(obj, ip, port):
    Pyro4.Daemon.serveSimple(
        {obj: "%s:%s" % (ip, str(port))}, host=ip, port=port, ns=False
    )

def get_hash(string):
    return int.from_bytes(hashlib.sha1(string.encode()).digest(), byteorder=sys.byteorder ) % (SIZE)

def hashb(data):
    return int.from_bytes(hashlib.sha1(data).digest(), byteorder=sys.byteorder ) % (SIZE)

def main():
    print("tools")
    a = ["0","1","2", "3", "4"]
    p = Pagin()
    p.build(a, "1")
    print(p.pages)


if __name__ == "__main__":
    main()