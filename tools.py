import Pyro4
import hashlib
import sys
import math as m



# SPECIAL_DHT_KEYS
maxclient = "#maxclient"
allfiles = "#allfiles"
idclient = "#idclient"
sizefile = "#sizef"
filestep = "#step"    #files in a particular step
maxstep = "#maxstep"  #max step created
lenstep = 50     #cant files in each step
LOGSIZE = 64
SIZE = 1<<LOGSIZE

# SPECIAL CONSTANTS
backlog = 50
bufsize = 1
totalP = 5 # the max number of pieces in download
histsize = 20
maxpage = 5



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
    return int.from_bytes(hashlib.sha1(data).digest(), byteorder=sys.byteorder )  % (SIZE)

def main():
    print("tools")
    a = ["0","1","2", "3", "4"]
    p = Pagin()
    p.build(a, "1")
    print(p.pages)


if __name__ == "__main__":
    main()
