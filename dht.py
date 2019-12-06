import Pyro4
from chord import *
import sys
import hashlib
import time

from tools import get_auto_addr, discover

from broadcast_server import *

maxclient = "#maxclient"
allfiles = "#allfiles"
filestep = "#step"    #files in a particular step
maxstep = "#maxstep"  #max step created

# def get_remote(ip_port):
#         uri = f"PYRO:{ip_port}@{ip_port}"
#         remote_node = Pyro4.Proxy(uri)
#         return remote_node

def CreateChordAutom(root = False):
    ip, port = get_auto_addr(8000, 9000)
    addr_father = None
    if not root:
        addr_father = discover(ip, port)
    return Node((ip, port), addr_father)

@Pyro4.expose
class DHT(object):
    def __init__(self):
        # self.d = {}
        self.nodes = []
        # self.nodes.append(Node(('192.168.43.124',8888)))
        # self.nodes.append(Node(('127.0.0.1',8009),('192.168.43.124',8888)))
        # self.nodes.append(Node(('127.0.0.1',8001),('192.168.43.124',8888)))
        # self.nodes.append(Node(('127.0.0.1',8003),('192.168.43.124',8888)))
        # self.nodes.append(Node(('127.0.0.1',8006),('192.168.43.124',8888)))
        # self.nodes.append(Node(('127.0.0.1',8004),('192.168.43.124',8888)))

        # self.nodes.append(Node(('127.0.0.1',8888)))
        # self.nodes.append(Node(('127.0.0.1',8009),('127.0.0.1',8888)))
        # self.nodes.append(Node(('127.0.0.1',8001),('127.0.0.1',8888)))
        # self.nodes.append(Node(('127.0.0.1',8003),('127.0.0.1',8888)))
        # self.nodes.append(Node(('127.0.0.1',8006),('127.0.0.1',8888)))
        # self.nodes.append(Node(('127.0.0.1',8004),('127.0.0.1',8888)))

        self.nodes.append(CreateChordAutom(True))
        time.sleep(1)
        self.nodes.append(CreateChordAutom())
        time.sleep(1)
        self.nodes.append(CreateChordAutom())

    def set(self, k, v):
        # self.d[k] = v
        # print(self.d)
        # print("\n")
        # print("****************************************************************")
        self.nodes[0].set(k,v)
        print("everybody ",self.get_all())

    def get(self, k):
        # return self.d.get(k)
        return self.nodes[0].get(k)

    def get_all(self):
        l = []
        for node in self.nodes:
            l.append(node.data)
        return l

    def get_sub_red(self):
        return [self.nodes[0].info] + self.nodes[0].successors

# def set_dht(key,value):
#     with get_remote('127.0.0.1:8888') as remote:
#         remote.set(key,value)


def main():
    d = DHT()
    d.set(get_hash(maxclient),0)
    d.set(get_hash(allfiles),[])
    d.set(get_hash(maxstep),0)
    d.set(get_hash(filestep + '|0'),[])
    while 1:
        time.sleep(10)
        print('******************************************************************************************')
        print(d.get_all())
        print("RED:\n",d.get_sub_red())



    # set_dht(get_hash(maxclient),0)
    # print(get_hash(maxclient))
    # set_dht(get_hash(allfiles),[])
    # print(get_hash(allfiles))
    # set_dht(get_hash(maxstep),0)
    # print(get_hash(maxstep))
    # set_dht(get_hash(filestep + '|0'),[])
    # print(get_hash(filestep + '|0'))

    # ## *** Test autodiscover
    # n1 = CreateChordAutom(True)
    # time.sleep(1)
    # n2 = CreateChordAutom()
    # ## ***
if __name__ == "__main__":
    main()
