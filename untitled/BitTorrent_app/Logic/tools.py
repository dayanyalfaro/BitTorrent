import Pyro4
import hashlib
import sys

from BitTorrent_app.Logic.settings import SIZE

# SPECIAL_DHT_KEYS
maxclient = "#maxclient"
allfiles = "#allfiles"
idclient = "#idclient"
sizefile = "#sizef"
filestep = "#step"    #files in a particular step
maxstep = "#maxstep"  #max step created
lenstep = 50     #cant files in each step
 # DHT size

# SPECIAL CONSTANTS
backlog = 50
bufsize = 1024*1024
totalP = 20  # the max number of pieces
histsize = 2


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

    import math
    a = math.log2(1024)
    print(a)
    print(math.log2(1024*1024))
    print(math.log2(1024*1024*1024))


if __name__ == "__main__":
    main()