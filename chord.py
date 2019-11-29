from threading import Lock

import Pyro4
import threading
import random
import hashlib
import time
import sys

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
                f(*args)
                # try:
                #     f(*args)
                # except:
                #     pass
                time.sleep(t)
        return wrapper
    return decorator


@Pyro4.expose
class Node:
    def __init__(self, local_address, remote_address: tuple = None):
        self.ip = local_address[0]
        self.port = local_address[1]

        self.id = f"{self.ip}:{self.port}"
        self.key = int.from_bytes(hashlib.sha1(self.id.encode()).digest(), byteorder= sys.byteorder) % SIZE
        self._info = {'id': self.id, 'key': self.key}

        # self.suc_lock = threading.Lock()
        self.pred_lock = threading.Lock()
        self.finger_lock = threading.Lock()
        self.data_lock = threading.Lock()
        self.replica_lock = threading.Lock()

        self._data = {}
        self._replica = {}

        self.start()

        if remote_address:
            self.join(remote_address)
        else:
            self.join()

        time.sleep(1)
        self.threads = {}
        self.threads['stabilize'] = ChordThread(self, 'stabilize', ())
        self.threads['update_successors'] = ChordThread(self, 'update_successors', ())
        self.threads['fix_fingers'] = ChordThread(self, 'fix_fingers', ())
        self.threads['replicate'] = ChordThread(self, 'replicate', ())
        for key in self.threads.keys():
            self.threads[key].start()

    # logging function
    def log(self, info:str):
        # pass
        f = open(f"{self.id}.log", "a+")
        f.write(str(info + "\n"))
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

    @property
    def data(self):
        return self._data

    @property
    def replica(self):
        return self._replica

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
            if self.isinrange(key,self.predecessor['key'],self.key):
                return self._data.get(key)
            else:
                return self._replica.get(key)

        with self.get_remote(info['id']) as remote:
            if self.isinrange(key, remote.predecessor['key'], remote.info['key']):
                return remote.data.get(key)
            else:
                return remote.replica.get(key)

    def set(self, key, value):
        self.log(f'setting {key}')
        print('inserting ' , key)
        info = self.find_successor(key)
        print('find_successor passed')
        if info['id'] == self.id:
            self.store_at_data(key, value)
        else:
            with self.get_remote(info['id']) as remote:
                remote.store_at_data(key, value)


    def store_at_replica(self, key, value):
        self.log(f'storing {key}')
        self.replica_lock.acquire()
        self._replica[key] = value
        self.replica_lock.release()

    def store_at_data(self, key, value):
        print('storing ', key, 'at' , self.id)
        self.data_lock.acquire()
        self._data[key] = value
        self.data_lock.release()
        
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

        # global debug
        # if debug:
        #     print('entering find_successor')
        # if the key belongs to this node
        if self._predecessor and \
        self.isinrange(key,self._predecessor['key'],self.key):
            self.log("find_successor")
            return self.info
        pred = self.find_predecessor(key)
        # if debug:
        #     print('find_predecessor passed')
        with self.get_remote(pred['id']) as pred_remote:
            self.log("find_successor")
            return pred_remote.get_successor()

    def find_predecessor(self, key):
        # global debug
        # if debug:
        #     print('entering find_predecessor')
        node = self.info
        successor = self.finger_table[0]

        # if there is only one node
        if successor['id'] == self.id:
            self.log("find_predecessor")
            return node

        while not self.isinrange(key, node['key'], successor['key']):
            with self.get_remote(node['id']) as node_remote:
                node = node_remote.closest_preceding_finger(key)
            with self.get_remote(node['id']) as node_remote:
                successor = node_remote.finger_table[0]

        self.log("find_predecessor")
        return node

    def closest_preceding_finger(self, key):
        # self.log("closest_preceding_finger")
        # fingers in decreasing distance
        for node in reversed(self._finger_table):
            if node:
                if self.isinrange(node['key'], self.key, key - 1) and \
                self.ping(node['id']):
                    self.log("closest_preceding_finger other " +  str(node['key']))
                    return node
        self.log("closest_preceding_finger me")
        return self.info

    @repeat_and_sleep(2)
    def stabilize(self):
        self.log("stabilize")

        # get first alive successor
        successor = self.get_successor()

        # update this node's successor in case it changed
        self.finger_lock.acquire()
        if successor['id'] != self.finger_table[0]['id']:
            self.finger_table[0] = successor
        self.finger_lock.release()

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
        # self.log("get_successor")
        for suc in [self._finger_table[0]] + self._successors:
            if self.ping(suc['id']):
                return suc
        return self.info

    @repeat_and_sleep(2)
    def update_successors(self):
        self.log("update_successors")

        suc = self.get_successor()
        # if we are not alone in the ring
        if suc['id'] != self.id:
            successors = [suc]
            with self.get_remote(suc['id']) as remote_suc:
                suc_list = remote_suc.successors
                successors += suc_list[0:LOGSIZE - 1]
                # in case the amount of nodes is less than or equal to LOGSIZE
                for i in range(len(successors)):
                    if successors[i] == self.info:
                        successors = successors[0:i]
                        break
                self._successors = successors


    def notify(self,node):
        self.log("notify")

        if not self._predecessor or \
        self.isinrange(node['key'], self._predecessor['key'], self.key) or \
        not self.ping(self._predecessor['id']):
            self.pred_lock.acquire()
            self._predecessor = node
            self.pred_lock.release()

            self.acquire_keys()
            self.give_keys()

    @repeat_and_sleep(2)
    def fix_fingers(self):
        i = random.randrange(LOGSIZE)
        self.log(f"fix_fingers at {i}")
        self.finger_lock.acquire()
        self._finger_table[i] = self.find_successor((self.key + 2**i)% SIZE)
        self.finger_lock.release()

    @repeat_and_sleep(10)
    def replicate(self):
        self.log("replicate")
        self.data_lock.acquire()
        for key in self._data.keys():
            for suc in self.successors:
                if self.ping(suc['id']):
                    with self.get_remote(suc['id']) as remote:
                        remote.store_at_replica(key, self._data[key])
        self.data_lock.release()

    def acquire_keys(self):
        to_del = []
        self.replica_lock.acquire()

        for key in self._replica.keys():
            if self.isinrange(key, self.predecessor['key'], self.key):

                self.data_lock.acquire()
                self._data[key] = self._replica[key]
                self.data_lock.release()
                to_del.append(key)

        for key in to_del:
            del self._replica[key]

        self.replica_lock.release()

    def give_keys(self):
        to_del = []
        self.data_lock.acquire()

        for key in self._data.keys():
            if not self.isinrange(key, self.predecessor['key'], self.key):
                with self.get_remote(self.predecessor['id']) as remote:
                    remote.store_at_data(key,self._data[key])
                    to_del.append(key)

        for key in to_del:
            del self._data[key]

        self.data_lock.release()


# a = Node(('127.0.0.1',8000)) # 0
# b = Node(('127.0.0.1',8001),('127.0.0.1',8000)) # 3
# c = Node(('127.0.0.1',8002),('127.0.0.1',8000)) # 1
# # d = Node(('127.0.0.1',8004),('127.0.0.1',8000))
# e = Node(('127.0.0.1',8009),('127.0.0.1',8000)) # 5
#
# a.set(2,4)
# a.set(4,16)
# a.set(6,36)
# a.set(7,49)
#
# lst = [a,c,b,e]
#
# while 1:
#     for n in lst:
#         print("_________________________________________________")
#         print(f"Node {n.info['key']}")
#         print("_________________________________________________")
#         print("data: ",n._data)
#         print("replica: ",n._replica)
#         time.sleep(5)

# while 1:
#     print ("___________________")
#     with a.get_remote('127.0.0.1:8000') as r:
#         print(r.info, r.finger_table[0], " | " ,  r.predecessor)
#     print ("___________________")
#     with a.get_remote('127.0.0.1:8001') as r:
#         print(r.info, r.finger_table[0],  " | " , r.predecessor)
#     print ("___________________")
#     with a.get_remote('127.0.0.1:8002') as r:
#         print(r.info, r.finger_table[0],  " | " , r.predecessor)
#     print ("___________________")
#     with a.get_remote('127.0.0.1:8004') as r:
#         print(r.info, r.finger_table[0], " | ", r.predecessor)
#     print("___________________")
#     # a.update_successors()
#     # b.update_successors()
#     # a.stabilize(),.
#     # b.stabilize()
#     # a.fix_fingers()
#     # b.fix_fingers()
#     time.sleep(5)

# if __name__ == "__main__":
#     import sys
#     if len(sys.argv) == 2:
#         port = int(sys.argv[1])
#         a = Node(('127.0.0.1',port))
#         while 1:
#             print ("___________________")
#             with a.get_remote(f'127.0.0.1:{port}') as r:
#                 # print(r.info, r.finger_table[0], " | " ,  r.predecessor)
#                 print(r.info)
#                 for i in range(len(r.finger_table)):
#                     print(((r.info['key'] + 2**i)% SIZE),' : ', r.finger_table[i])
#             print ("___________________")
#             time.sleep(5)
#
#     else:
#         port_root = int(sys.argv[1])
#         port = int(sys.argv[2])
#         a = Node(('127.0.0.1', port),('127.0.0.1', port_root))
#         while 1:
#             print("___________________")
#             with a.get_remote(f'127.0.0.1:{port}') as r:
#                 # print(r.info, r.finger_table[0], " | ", r.predecessor)
#                 print(r.info)
#                 for i in range(len(r.finger_table)):
#                     print(((r.info['key'] + 2**i) % SIZE), ' : ', r.finger_table[i])
#             print("___________________")
#             time.sleep(5)


if __name__ == "__main__":
    import sys
    debug = False
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
        a = Node(('127.0.0.1',port))
        while 1:
            print("_________________________________________________")
            print(f"Node {a.info['key']}")
            print("_________________________________________________")
            print("data: ",a._data)
            print("replica: ",a._replica)
            print("_________________________________________________")
            print("predecessor : ", a._predecessor)
            print("_________________________________________________")
            with a.get_remote(f'127.0.0.1:{port}') as r:
                for i in range(len(r.finger_table)):
                    print(((r.info['key'] + 2**i) % SIZE), ' : ', r.finger_table[i])
            print("_________________________________________________")
            print("threads :")
            for key in a.threads.keys():
                print(key, a.threads[key].is_alive())
            print("_________________________________________________")
            time.sleep(5)

    else:
        port_root = int(sys.argv[1])
        port = int(sys.argv[2])
        a = Node(('127.0.0.1', port),('127.0.0.1', port_root))
        count = 0
        while 1:
            count += 1
            if port == 8004 and count == 10:
                debug = True
                a.set(2, 4)
                print('2 inserted')
                a.set(4, 16)
                print('4 inserted')
                a.set(6, 36)
                print('6 inserted')
                a.set(8, 64)
                print('8 inserted')
                a.set(12, 144)
                print('12 inserted')
                a.set(14, 196)
                print('14 inserted')
                debug = False
            # if count == 20 or count == 30:
            #     suc = a.find_successor(4)
            #     print('FIND_SUCCESSOR(4) =====>   ',suc)
            print("_________________________________________________")
            print("_________________________________________________")
            print(f"Node {a.info['key']}", '     COUNT: ',count)
            print("_________________________________________________")
            print("data: ",a._data)
            print("replica: ",a._replica)
            print("_________________________________________________")
            print("predecessor : ",a._predecessor)
            print("_________________________________________________")
            with a.get_remote(f'127.0.0.1:{port}') as r:
                for i in range(len(r.finger_table)):
                    print(((r.info['key'] + 2**i) % SIZE), ' : ', r.finger_table[i])
            print("_________________________________________________")
            print("threads :")
            for key in a.threads.keys():
                print(key, a.threads[key].is_alive())
            print("_________________________________________________")
            time.sleep(5)



# a = Node(('127.0.0.1',8000)) # 0
# e = Node(('127.0.0.1',8009),('127.0.0.1',8000)) # 13
# d = Node(('127.0.0.1',8001),('127.0.0.1',8000)) # 11
# b = Node(('127.0.0.1',8003),('127.0.0.1',8000)) # 3
# c = Node(('127.0.0.1',8006),('127.0.0.1',8000)) # 7
# e = Node(('127.0.0.1',8004),('127.0.0.1',8000)) # 15
#
#
# time.sleep(20)
# debug = True
# e.set(2, 4)
# print('2 inserted')
# e.set(4, 16)
# print('4 inserted')
# e.set(6, 36)
# print('6 inserted')
# e.set(8, 64)
# print('8 inserted')
# e.set(12, 144)
# print('12 inserted')
# e.set(14, 196)
# print('14 inserted')

