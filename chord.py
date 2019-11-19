import Pyro4
import threading
import random
import hashlib
import sys
import time
import ctypes

from settings import *


class ChordThread(threading.Thread):
    def __init__(self, obj, method, args):
        threading.Thread.__init__(self)
        self.obj_ = obj
        self.method_ = method
        self.args = args

    def run(self):
        getattr(self.obj_, self.method_)(*self.args)



def repeat_and_sleep(t):
    def decorator(f):
        def wrapper(*args):
            while 1:
                try:
                    f(*args)
                except:
                    pass
                time.sleep(t)
        return wrapper
    return decorator


@Pyro4.expose
class Node:
    def __init__(self, local_address, remote_address: tuple = None):
        self.ip = local_address[0]
        self.port = local_address[1]

        self.id = f"{self.ip}:{self.port}"
        self.key = int.from_bytes(hashlib.sha1(self.id.encode()).digest(), byteorder=sys.byteorder) % SIZE
        self._info = {'id': self.id, 'key': self.key}

        self.lock = threading.Lock()
        self.data = {}

        self.start()

        if remote_address:
            self.join(remote_address)
        else:
            self.join()

        time.sleep(1)
        ChordThread(self, 'stabilize', ()).start()
        ChordThread(self, 'update_successors', ()).start()
        ChordThread(self, 'fix_fingers', ()).start()
         
    # logging function
    def log(self, info:str):
        f = open("chord.log", "a+")
        f.write(str(self.id) + " : " +  info + "\n")
        f.close()

    @property
    def info(self):
        return self._info

    @property
    def finger_table(self):
        return self._finger_table

    @property
    def successors(self):
        return self._successors

    @property
    def predecessor(self):
        return self._predecessor

    @staticmethod
    def isinrange(obj, start, end):
        """ obj is in (start,end] """
        if start == end:
            return True
        if start < end:
            return obj > start and obj <= end
        return start < obj or obj <= end

    @staticmethod
    def get_remote(ip_port):
        uri = f"PYRO:{ip_port}@{ip_port}"
        remote_node = Pyro4.Proxy(uri)
        return remote_node

    def start(self):
        self.thread = ChordThread(self,'start_service',(self.ip,self.port))
        self.thread.start()

    def start_service(self,ip,port):
        Pyro4.Daemon.serveSimple(
        {
            self : f"{ip}:{port}"
        },
        host = ip,
        port = port,
        ns = False

    )     

    def get(self, key):
        info = self.find_successor(key)

        if info['id'] == self.id:
            return self.data.get(key)

        with self.get_remote(info['id']) as remote:
            return remote.data.get(key)

    def set(self, key, value):
        info = self.find_successor(key)

        self.lock.acquire()

        if info['id'] == self.id:
            self.data[key] = value
        else:
            with self.get_remote(info['id']) as remote:
                remote.data[key] = value

        self.lock.release()

        
    def join(self, remote_address = None):
        self.log("joined")

        self._successors = []
        self._finger_table = [None for _ in range(LOGSIZE)]
        self._predecessor = None

        if remote_address:
            with self.get_remote(f"{remote_address[0]}:{remote_address[1]}") as remote:
                self._finger_table[0] = remote.find_successor(self.key)
        else:
            self._finger_table[0] = self.info

        self._successors = [self.finger_table[0]]

    def ping(self, remote_address = None):
        if not remote_address:
            return True
        try:
            with self.get_remote(remote_address) as remote:
                return remote.ping()
        except:
            return False

    def find_successor(self, key):
        self.log("find_successor")

        # if the key belongs to this node
        if self._predecessor and \
        self.isinrange(key,self._predecessor['key'],self.key):
            return self.info
        
        pred = self.find_predecessor(key)
        with self.get_remote(pred['id']) as pred_remote:
            return pred_remote.get_successor()

    def find_predecessor(self, key):
        self.log("find_predecessor")

        node = self.info
        successor = self.finger_table[0]

        # if there is only one node
        if successor['id'] == self.id:
            return node

        while not self.isinrange(key, node['key'], successor['key']):
            node = self.closest_preceding_finger(key)
            with self.get_remote(node['id']) as node_remote:
                successor = node_remote.finger_table[0]

        return node

    def closest_preceding_finger(self, key):
        self.log("closest_preceding_finger")

        # fingers in decreasing distance
        for node in reversed(self._finger_table):
            if self.isinrange(node['key'],self.key,key) and \
            self.ping(node['id']):
                return node
        return self.info

    @repeat_and_sleep(1)
    def stabilize(self):
        self.log("stabilize")

        # get first alive successor
        successor = self.get_successor()

        self.lock.acquire()
        # update this node's successor in case it changed
        if successor['id'] != self.finger_table[0]['id']:
            self.finger_table[0] = successor
        self.lock.release()

        successor_remote = self.get_remote(successor['id'])
        # get predecessor of my successor
        pred_successor = successor_remote.predecessor

        # if the predecessor of my successor is closer to me than my successor
        if pred_successor and \
        self.isinrange(pred_successor['key'], self.key, successor['key']) and \
        self.ping(pred_successor['id']):
            successor = self._finger_table[0] = pred_successor
            successor_remote = self.get_remote(successor['id'])
            
        successor_remote.notify(self.info)

    def get_successor(self):
        self.log("get_successor")
        for suc in [self._finger_table[0]] + self._successors:
            if self.ping(suc['id']):

                # self.lock.acquire()
                # self._finger_table[0] = suc
                # self.lock.release()

                return suc

        # self.lock.acquire()
        #
        # self._finger_table[0] = self.info
        # self.successors = [self.info]
        #
        # self.lock.release()

        return self.info

    @repeat_and_sleep(1)
    def update_successors(self):
        self.log("update_successors")
        suc = self.get_successor()
        # if we are not alone in the ring
        if suc['id'] != self.id:
            successors = [suc]
            with self.get_remote(suc['id']) as remote_suc:
                suc_list = remote_suc.successors
                if suc_list and len(suc_list):
                    successors += suc_list
                self._successors = successors


    def notify(self,node):
        self.log("notify")

        if not self._predecessor or \
        self.isinrange(node['key'],self._predecessor['key'],self.key) or \
        not self.ping(self._predecessor['id']):
            self.lock.acquire()
            self._predecessor = node
            self.lock.release()

    @repeat_and_sleep(1)
    def fix_fingers(self):
        i = random.randrange(LOGSIZE)
        self.lock.acquire()
        self._finger_table[i] = self.find_successor((self.key + 1<<i)% SIZE)
        self.lock.release()

a = Node(('127.0.0.1',8000))
b = Node(('127.0.0.1',8001),('127.0.0.1',8000))
c = Node(('127.0.0.1',8002),('127.0.0.1',8000))
d = Node(('127.0.0.1',8004),('127.0.0.1',8000))


while 1:
    print ("___________________")
    with a.get_remote('127.0.0.1:8000') as r:
        print(r.info, r.finger_table[0], " | " ,  r.predecessor)
    print ("___________________")
    with a.get_remote('127.0.0.1:8001') as r:
        print(r.info, r.finger_table[0],  " | " , r.predecessor)
    print ("___________________")
    with a.get_remote('127.0.0.1:8002') as r:
        print(r.info, r.finger_table[0],  " | " , r.predecessor)
    print ("___________________")
    with a.get_remote('127.0.0.1:8004') as r:
        print(r.info, r.finger_table[0], " | ", r.predecessor)
    print("___________________")
    # a.update_successors()
    # b.update_successors()
    # a.stabilize()
    # b.stabilize()
    # a.fix_fingers()
    # b.fix_fingers()
    time.sleep(5)