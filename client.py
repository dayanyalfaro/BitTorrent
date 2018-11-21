import socket
from select import select
import Pyro4
import os
import time
from middleware import Comunicator
from transaction import Transaction, Download
from tools import *
from threading import Thread


class Client(object):
    def __init__(self, ip, port, dht_ip, dht_port, path, addr_listen):
        self.c_id = None
        self.ip = ip
        self.port = port
        self.path = path
        self.comunicator = Comunicator(addr_listen, dht_ip, dht_port)
        self.download = {}
        self.max_dwn = 0
        self.pending = []
        self.fd_dic = {}
        self.pub = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addr_listen = addr_listen

        try:
            os.mkdir(self.path)
        except:
            pass

        self.set_id()

        Thread(target=self.start_listen, args=()).start()

    def connect_to_peer(self, addr):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(addr)
        return s

    def start_listen(self):
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(self.addr_listen)
        self.sock.listen(backlog)
        print(">Client " + str(self.c_id) + " is listening on ", self.addr_listen)

        pend_to_attend = [self.sock]

        while True:
            inputs = [t.fi for t in self.pending if not t.is_load] + pend_to_attend
            outputs = [t.fo for t in self.pending if t.is_load]

            rfd, wfd, efd = select(inputs, outputs, [], 2)
            for s in rfd:
                if s == self.sock:
                    conn, addr = self.sock.accept()
                    print(
                        ">Client " + str(self.c_id) + " got connection from -> ", addr
                    )
                    pend_to_attend.append(conn)
                elif s in pend_to_attend:
                    self.attend_client(s)
                    pend_to_attend.remove(s)
                else:  # arreglar
                    self.fd_dic[s].read()

            for s in wfd:  # arreglar
                self.fd_dic[s].write()

            self.pending = [i for i in self.pending if not i.finish and not i.is_fail]

    def attend_client(self, s):
        rqs = self.parse_rqs(s)
        print(">Attend client -> ", rqs)

        if rqs[0] == "GET":
            try:
                offset = int(rqs[2])  # open file start in the offset
                fo = open(self.path + "/" + rqs[1], "rb")
                fo.seek(offset)  # open a file in a specific position
                size = int(rqs[3])  # size of the porcion of the file to send
                if size == -1:  # send complete file
                    size = self.get_len_file(rqs[1])  #
                print(size)
                rps = "%d|%s" % (len(str(size)), str(size))
                s.send(rps.encode())
                self.create_transaction(fo, s, "send", size)
            except:
                s.send("2|-1".encode())
        if rqs[0] == "HAS":
            try:
                fo = open(self.path + "/" + rqs[1], "rb")
                size = self.get_len_file(rqs[1])  # send the size of the file
                rps = "%d|%s" % (len(str(size)), str(size))
                s.send(rps.encode())
            except:
                s.send("2|-1".encode())

    def dwn_file(self, file_name):
        potencial_loc = self.potencial_location(file_name)
        print("BEFORE DWNLOAD", potencial_loc)
        for p in potencial_loc:
            self.dwn_file_from_peer(file_name, p[0], 1, 2, -1, -1)
            try:
                f = open(self.path + "/" + file_name, "rb")
                print(">Client:" + str(self.c_id) + "download file" + file_name)
                self.publish(file_name, self.get_len_file(file_name))
                break
            except:
                pass

    def potencial_location(self, file_name):  # ok
        location = self.get_file_location(file_name)
        p = []
        for l in location:
            start = time.clock()
            r = self.has_file(file_name, l)
            delta = time.clock() - start
            p.append((l, delta, r))  # (node, timeout, has_file?)

        l = [node for node in p if node[2]]
        l = sorted(l, key=lambda tup: tup[1])  # sort by the timeout
        l = [n[0] for n in l]
        return l

    def has_file(self, file_name, addr):  # ok
        size = -1
        try:
            s = self.connect_to_peer(addr)
            print("connected to ask HAS FILE")
            rqs = "HAS|" + file_name
            rqs = "%d|%s" % (len(rqs), rqs)
            s.send(rqs.encode())
            size = int(self.parse_rqs(s)[0])
        except:
            pass
        return size >= 0

    def Download(self, file_name):
        location = self.potencial_location(file_name)

        dwn = Download(self.max_dwn, file_name, self.get_len_file(file_name))
        self.max_dwn += 1
        self.download[dwn.id] = dwn
        dwn.build(location)

        # for i in len(dwn.pieces):
        #     p = dwn.pieces[i]
        #     self.dwn_file_from_peer(file_name, p.offset, )

    def dwn_file_from_peer(self, file_name, addr, offset, dwn_size, dwn_id, piece_id):
        s = self.connect_to_peer(addr)

        rqs = "GET|" + file_name + "|" + str(offset) + "|" + str(dwn_size)
        rqs = "%d|%s" % (len(rqs), rqs)
        s.send(rqs.encode())

        try:
            fo = open(self.path + "/" + file_name + str(piece_id), "wb")
            self.create_transaction(s, fo, "dwn", dwn_size, dwn_id, piece_id)
        except:
            pass

    def parse_rqs(self, s):  # ok
        d = s.recv(1).decode()
        l = ""
        while d:
            if d == "|":
                l = int(l)
                break
            l += d
            d = s.recv(1).decode()
        rqs = s.recv(l).decode()
        rqs = str(rqs).split("|")
        return rqs

    def create_transaction(self, fi, fo, type_t, size, dwn_id, piece_id):
        t = Transaction(fi, fo, type_t, size, dwn_id, piece_id)
        self.pending.append(t)
        self.fd_dic[fi] = t
        self.fd_dic[fo] = t

    def set_id(self):  # ok
        if self.c_id == None:
            try:
                f = open(self.path + "/id", "r")
                self.c_id = int(f.read(1024))
                self.comunicator.update_idclient(self.c_id, self.addr_listen)
                f.close()
            except:
                self.c_id = self.comunicator.get_id()
                try:
                    r = self.path + "/id"
                    f = open(r, "w")
                    f.write(str(self.c_id))
                    print("client with id:" + str(self.c_id) + " was created")
                    f.close()
                except:
                    print("no id file open")

    def copy_file_from_directory(self, p_source, name):
        p_dest = self.path + "/" + name

        def copy():
            try:
                fi = open(p_source, "rb")
                fo = open(p_dest, "wb")
                d = fi.read(bufsize)
                size = 0
                while d:
                    fo.write(d)
                    size += len(d)
                    d = fi.read(bufsize)
                self.publish(name, size)
                fi.close()
                fo.close()
            except:
                print("error: failed open file in copy from a directory")

        self.pub.append(Thread(target=copy, args=()))
        self.pub[-1].start()

    def get_len_file(self, file_name):
        return self.comunicator.get_len_file(file_name)

    def publish(self, name, size):
        torrent = name
        self.comunicator.publish(torrent, self.c_id, size)

    def get_file_location(self, file):
        nodes = self.comunicator.get_location(file)
        return nodes

    def see_files(self):
        self.comunicator.all_files()


def main():
    print("hello")


if __name__ == "__main__":
    main()