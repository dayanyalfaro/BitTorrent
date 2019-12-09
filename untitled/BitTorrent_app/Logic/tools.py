import Pyro4
import hashlib
import sys


# SPECIAL_DHT_KEYS
maxclient = "#maxclient"   #max id to set a client
allfiles = "#allfiles"
myfiles = "#files"
idclient = "#idclient"
sizefile = "#sizef"
filestep = "#step"    #files in a particular step
maxstep = "#maxstep"  #max step created
lenstep = 100     #cant files in each step
LOGSIZE = 64
SIZE = 1<<LOGSIZE

# SPECIAL CONSTANTS
backlog = 100        #listen number
bufsize = 10*1024
totalP = 20 # the max number of pieces in download


def verify_dht_conexion(func):
    def wrapper(self, *args, **kwargs):
        try:
            with get_remote_node(self.comunicator.dht_ip, self.comunicator.dht_port) as remote:
                remote.ping()
        except:
            actual_node = [self.comunicator.dht_ip, str(self.comunicator.dht_port)]
            if actual_node in self.dht_nodes:
                self.dht_nodes.remove(actual_node)
            if self.dht_nodes:
                self.comunicator.update_dht(self.dht_nodes[0][0], self.dht_nodes[0][1])
        return func(self, *args, **kwargs)
    return wrapper


def mutex_rlock(f):
    def wrapper(self, *args, **keyargs):
        self.lock.acquire()
        r = f(self, *args, **keyargs)
        self.lock.release()
        return r
    return wrapper


def get_remote_node(ip, port):
    uri = "PYRO:" + ip + ":" + str(port) + "@" + ip + ":" + str(port)
    p = Pyro4.Proxy(uri)
    return p

######## AutoDiscover tool

from BitTorrent_app.Logic.multicast import listen_loop
from BitTorrent_app.Logic.multicast import announce_loop
from BitTorrent_app.Logic.multicast import get_local_ip
import time
from socket import *


def discover(ipban, portban):
    for msg in listen_loop():
        ip, port = msg.split()
        if ip == ipban and int(portban) == int(port):
            continue
        try:
            node = get_remote_node(ip, port)
            if node.ping():
                return (ip, int(port))
        except:
            pass

def announce(ip, port):
    msg = "%s %s" % (ip, str(port))
    announce_loop(msg)

def get_ip():
    return get_local_ip()[0]

def get_free_port(ip, bport, eport):
    for port in range(bport, eport + 1):
        # try:
        client = socket(AF_INET, SOCK_STREAM)
        conexion = client.connect_ex((ip, port))
        # print(conexion)
        if (conexion != 0):
            client.close()
            time.sleep(2)
            return port
        else:
            client.close()
    return -1

def get_auto_addr(bport, eport):
    ip = get_local_ip()[0]
    port = get_free_port(ip, bport, eport)
    return (ip, int(port))

########### end autodiscover

def start_service(obj, ip, port):
    Pyro4.Daemon.serveSimple(
        {obj: "%s:%s" % (ip, str(port))}, host=ip, port=port, ns=False
    )

def get_hash(string):
    return int.from_bytes(hashlib.sha1(string.encode()).digest(), byteorder=sys.byteorder ) % (SIZE)

def hashb(data):
    return int.from_bytes(hashlib.sha1(data).digest(), byteorder=sys.byteorder )  % (SIZE)

def remove_accents(text):
    import unicodedata
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    return str(text)


def main():
    print("tools")


if __name__ == "__main__":
    main()
