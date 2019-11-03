import Pyro4
import threading
import random

from settings import *

def isinrange(obj,start,end):
    """ obj is in (start,end] """
    return obj > start and obj <= end

class ChordThread(threading.Thread):
    def __init__(self, obj, method, args):
        threading.Thread.__init__(self)
        self.obj_ = obj
        self.method_ = method
        self.args = args

    def run(self):
        getattr(self.obj_, self.method_)(*self.args)   

@Pyro4.expose
@Pyro4.callback
class Node:
    def __init__(self, local_address, remote_address:tuple = None):
        self.ip = local_address[0]
        self.port = local_address[1]

        self.id = f"{self.ip}:{self.port}"
        self.key = hash(self.id)
        self.info = {'id':self.id, 'key':self.key}

        self.successors = []

        if remote_address:
            self.join(remote_address)
        else:
            self.join()
         
	# logging function
    # def log(self, info:str):
    #     f = open("/tmp/chord.log", "a+")
    #     f.write(str(self.id) + " : " +  info + "\n")
    #     f.close()

    def start(self):
        ChordThread(self,'start_service',(self.ip,self.port)).start()

    def start_service(self,ip,port):
        Pyro4.Daemon.serveSimple(
        {
            self : f"{ip}:{port}"
        },
        host = ip,
        port = port,
        ns = False
    )     
    def get_remote(self,ip_port):
        uri = f"PYRO:{ip_port}@{ip_port}"
        remote_node = Pyro4.Proxy(uri)
        return remote_node

    def join(self,remote_address = None):
        self.finger_table = {}
        self.predecessor = None

        if remote_address:
            remote = self.get_remote(f"{remote_address[0]}:{remote_address[1]}")
            self.finger_table[0] = remote.find_successor(self.key)
        else:
            self.finger_table[0] = self.info
        
        # self.log("joined")

    def ping(self):
        return True

    def find_successor(self,key):
        if self.predecessor and \
        isinrange(key,self.predecessor['key'],self.key):
            return self.info
        pred = self.find_predecessor(key)
        pred_remote = self.get_remote(pred['id'])
        return pred_remote.get_successor()

    def find_predecessor(self,key):
        node = self.info
        successor = self.finger_table[0]
        if successor['id'] == self.id:
            return node
        while not isinrange(key,node['key'],successor['key']):
            node = self.closest_preceding_finger(key)
            node_remote = self.get_remote(node['id'])
            successor = node_remote.finger_table[0]
        return node

    def closest_preceding_finger(self,key):
        for i in range(LOGSIZE - 1,-1,-1):
            if isinrange(self.finger_table[i]['key'],self.key,key):
                return self.finger_table[i]
        return self.info

    def stabilize(self):
        successor = self.get_successor()

        if successor['id'] != self.finger_table[0]['id']:
            self.finger_table[0] = successor
        
        successor_remote = self.get_remote(successor['id'])
        pred_succesor = successor_remote.predecessor

        if pred_succesor and \
        isinrange(pred_succesor['key'], self.key, successor['key']) and \
        self.get_remote(pred_succesor['id']).ping():
            successor = self.finger_table[0] = pred_succesor
            successor_remote = self.get_remote(successor['id'])
        successor_remote.notify(self.info)
        
        # self.log("stabilize")

    def get_successor(self):
        for suc in [self.finger_table[0]] + self.successors:
            remote = self.get_remote(suc['id'])
            if remote.ping():
                self.finger_table[0] = suc
                return suc 
        return self.info

    def update_successors(self):
        suc = self.get_successor()
        # if we are not alone in the ring
        if suc['id'] != self.id:
            successors = [suc]
            remote_suc = self.get_remote(suc['id'])
            suc_list = remote_suc.successors
            if suc_list and len(suc_list):
                successors += suc_list
            self.successors = successors


    def notify(self,node):
        if not self.predecessor or \
        isinrange(node['key'],self.predecessor['key'],self.key) or \
        not self.get_remote(self.predecessor['id']).ping():
            self.predecessor = node 

        # self.log("notify")

    def fix_fingers(self):
        i = random.randrange(LOGSIZE - 1) + 1
        self.finger_table[i] = self.find_successor((self.key + 1<<i)% SIZE)


