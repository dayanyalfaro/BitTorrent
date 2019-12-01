import Pyro4
from chord import *
from tools import *


@Pyro4.expose
class DHT(object):
    def __init__(self):
        # self.d = {}
        self.nodes = []
        self.nodes.append(Node(('192.168.43.124',8888)))
        self.nodes.append(Node(('127.0.0.1',8009),('192.168.43.124',8888)))
        self.nodes.append(Node(('127.0.0.1',8001),('192.168.43.124',8888)))
        self.nodes.append(Node(('127.0.0.1',8003),('192.168.43.124',8888)))
        self.nodes.append(Node(('127.0.0.1',8006),('192.168.43.124',8888)))
        self.nodes.append(Node(('127.0.0.1',8004),('192.168.43.124',8888)))


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


def main():
    # print("hello")
    d = DHT()
    # d.d[hash("#maxclient")] = 0
    d.set(hash(maxclient),0)
    # d.d[hash("#allfiles")] = []
    d.set(hash(allfiles),[])
    # print(d.d)
    # ip = "localhost"  # change
    # port = 8888
    # start_service(d, ip, port)
    while 1:
        time.sleep(10)
        print('******************************************************************************************')
        print(d.get_all())
main()
