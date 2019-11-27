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
bufsize = 10
totalP = 20  # the max number of pieces


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

    f = open("./hello", "rb")
    d = f.read(10)
    print(d.decode())
    print(hash(d.decode()))
    print(hashb(d))

if __name__ == "__main__":
    main()