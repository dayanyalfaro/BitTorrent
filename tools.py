import Pyro4
import hashlib
import sys

# SPECIAL_DHT_KEYS
maxclient = "#maxclient"
allfiles = "#allfiles"
idclient = "#idclient"
sizefile = "#sizef"
SIZE = 20 # DHT size

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

def hash(string):
    return int.from_bytes(hashlib.sha1(string.encode()).digest(), byteorder=sys.byteorder ) % (1 << SIZE)

def hashb(data):
    return int.from_bytes(hashlib.sha1(data).digest(), byteorder=sys.byteorder ) % (1 << SIZE)

def main():
    print("tools")

    import math
    a = math.log2(1024)
    print(a)
    print(math.log2(1024*1024))
    print(math.log2(1024*1024*1024))


if __name__ == "__main__":
    main()