import Pyro4
from chord import *
import sys
import hashlib
import time
from tools import get_auto_addr, discover

maxclient = "#maxclient"
allfiles = "#allfiles"
filestep = "#step"    #files in a particular step
maxstep = "#maxstep"  #max step created

def CreateChordAutom(root = False):
    ip, port = get_auto_addr(8000, 9000)
    addr_father = None
    if not root:
        addr_father = discover(ip, port)
    return Node((ip, port), addr_father)

@Pyro4.expose
class DHT(object):
    def __init__(self):
        self.nodes = []
        self.nodes.append(CreateChordAutom(True))
        time.sleep(1)
        self.nodes.append(CreateChordAutom())
        time.sleep(1)
        self.nodes.append(CreateChordAutom())

    def get_all(self):
        l = []
        for node in self.nodes:
            l.append(node.data)
        return l

    def get_sub_red(self):
        return [self.nodes[0].info] + self.nodes[0].successors



def main():
    d = DHT()
    time.sleep(10)
    d.nodes[0].set(get_hash(maxclient),0)
    d.nodes[0].set(get_hash(allfiles),[])
    d.nodes[0].set(get_hash(maxstep),0)
    d.nodes[0].set(get_hash(filestep + '|0'),[])
    while 1:
        time.sleep(10)
        print('******************************************************************************************')
        print(d.get_all())
        print("RED:\n",d.get_sub_red())



    # ## *** Test autodiscover
    # n1 = CreateChordAutom(True)
    # time.sleep(1)
    # n2 = CreateChordAutom()
    # ## ***
if __name__ == "__main__":
    main()
