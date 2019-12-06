import os
from socket import *
import time
import torrent_parser
import json
import random as r
from select import select
from threading import Thread

from BitTorrent_app.Logic.middleware import Comunicator
from BitTorrent_app.Logic.tools import *
from BitTorrent_app.Logic.transaction import Transaction, Download

def verify_dht_conexion(func):
    def wrapper(self,*args,**kwargs):
        try:
            with get_remote_node(self.comunicator.dht_ip,self.comunicator.dht_port) as remote:
                remote.ping()
        except:
            actual_node = [self.comunicator.dht_ip,str(self.comunicator.dht_port)]
            if actual_node in self.dht_nodes:
                self.dht_nodes.remove(actual_node)
            if self.dht_nodes:
                self.comunicator.update_dht(self.dht_nodes[0][0],self.dht_nodes[0][1])
        return func(self,*args,**kwargs)
    return wrapper

class Client(object):
    def __init__(self, dht_ip, dht_port, path, addr_listen):
        self.c_id = None
        self.path = path
        self.comunicator = Comunicator(addr_listen, dht_ip, dht_port)
        self.download = {}
        self.dwn_in_progress = []
        self.max_dwn = 0
        self.pending = []
        self.fd_dic = {}
        self.fd_to_close = []
        self.pub = []
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.addr_listen = addr_listen
        self.dht_nodes = self.comunicator.get_alternative_nodes()



        try:
            os.mkdir(self.path)
        except:
            print("no open Storage")

        self.set_id()

        self.files = self.load_my_files()


        Thread(target=self.start_listen, args=()).start()


    def connect_to_peer(self, addr):
        s = socket(AF_INET, SOCK_STREAM)
        s.connect(addr)
        return s

    def start_listen(self): #TODO poner lindo  el metodo
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.sock.bind(self.addr_listen)
        self.sock.listen(backlog)
        print(">Client " + str(self.c_id) + " is listening on ", self.addr_listen)

        # fd_to_close = []
        pend_to_attend = [self.sock]

        while True:

            inputs = pend_to_attend + [t.fi for t in self.pending if not t.is_load]
            outputs = [t.fo for t in self.pending if t.is_load]
            inputs = inputs[:512]
            outputs = outputs[:512]

            rfd, wfd, efd = select(inputs, outputs, [], 2)

            for s in rfd:
                if s == self.sock:
                    conn, addr = self.sock.accept()
                    pend_to_attend.append(conn)
                elif s in pend_to_attend:
                    if(self.attend_client(s)):
                        self.fd_to_close.append((s,time.clock()))
                    pend_to_attend.remove(s)
                else:
                    t = self.fd_dic[s] #TODO method Do_read_transaction
                    self.read_transaction(t)


            for s in wfd:

                t = self.fd_dic[s] #TODO method Do_write_transaction
                self.write_transaction(t)


            self.update_pending()
            self.update_fd_to_close()


    def read_transaction(self, t):
        t.read()

        if t.type == "dwn":
            dwn = self.download[t.dwn_id]

            if t.is_fail:
                restart = dwn.restart_piece(t.piece_id)
                print("Intent restart", restart)

                if not restart:
                    print("Download of " + dwn.file_name + "FAILED")
                    self.update_dwn_state(dwn, fail=True)

                else:  # si se pudo arreglar => se encargara otro nodo de ese piece
                    p = dwn.pieces[t.piece_id]
                    self.dwn_file_from_peer(dwn.file_name, p.attendant, p.offset, p.size, dwn.id, p.id)

    def write_transaction(self, t):
        t.write()

        if t.type == 'dwn':
            dwn = self.download[t.dwn_id]
            if t.finish:  # TODO delete t.fi, t.fo from fd_dic
                check = self.check_piece_with_torrent(t.piece_id, t.data_dwn, t.size,
                                                      dwn.file_name)  # check if the piece is correct
                if check:
                    print(dwn.file_name, "SUCCESS Piece:", t.piece_id)
                    next_p = dwn.success_piece(t.piece_id)
                    if next_p != -1:
                        try:  # intent download the next piece
                            self.dwn_file_from_peer(dwn.file_name, next_p.attendant, next_p.offset, next_p.size, dwn.id,
                                                    next_p.id)
                            print(dwn.file_name + " Piece:" + str(next_p.id) + " -->  ", next_p.attendant, "Size: ",
                                  next_p.size)
                        except:
                            print(">FAIL Piece", next_p.id, next_p.attendant)
                            restart = dwn.restart_piece(
                                next_p.id)  # TODO  ver si no se puede restart, xq el file ya no esta disponible

                            if not restart:
                                print("Download of " + dwn.file_name + "FAILED")
                                self.update_dwn_state(dwn, fail=True)

                            else:
                                print(dwn.file_name + "Restart done Piece:" + str(next_p.id) + " -->  ",
                                      next_p.attendant, "Size: ", next_p.size)
                                self.dwn_file_from_peer(dwn.file_name, next_p.attendant, next_p.offset, next_p.size,
                                                        dwn.id, next_p.id)

                    if dwn.is_finish():  # if all pieces done ==> publish file
                        print(dwn.file_name, " Download finished")
                        self.update_dwn_state(dwn, finish=True)
                        self.reconstruct_file(dwn.file_name, len(dwn.pieces))
                else:
                    print("Incorrect Piece was download")
                    os.remove(self.path + "/" + dwn.file_name + str(t.piece_id))
                    restart = dwn.restart_piece(t.piece_id)

                    if not restart:
                        print("Download of " + dwn.file_name + "FAILED")
                        self.update_dwn_state(dwn, fail=True)
                    else:
                        p = dwn.pieces[t.piece_id]
                        self.dwn_file_from_peer(dwn.file_name, p.attendant, p.offset, p.size, dwn.id, p.id)
            if t.is_fail:
                restart = dwn.restart_piece(t.piece_id)
                print("Intent restart", restart)
                if not restart:
                    print("Download of " + dwn.file_name + "FAILED")
                    self.update_dwn_state(dwn, fail=True)

                else:
                    p = dwn.pieces[t.piece_id]
                    self.dwn_file_from_peer(dwn.file_name, p.attendant, p.offset, p.size, dwn.id, p.id)

        else:  # type = 'send'
            if t.finish:
                self.fd_to_close.append((t.fo, time.clock()))

    def update_pending(self):
        for i in self.pending:
            i.validate_timeout(15)
            if i.type == "dwn":
                if self.download[i.dwn_id].state == "pause":
                    print("Pause dwn", i.dwn_id, i.piece_id)
                    i.close()
                if self.download[i.dwn_id].state == "cancel" :
                    print("Cancel dwn", i.dwn_id, i.piece_id)
                    i.close()

        self.pending = [i for i in self.pending if not i.finish and not i.is_fail and not (
            (i.type == "dwn") and (self.download[i.dwn_id].state == "pause" or self.download[i.dwn_id].state == "cancel" ))]

    def update_fd_to_close(self):
        fd_to_close_new = []
        for x in self.fd_to_close:  # closing open socket
            fd, fd_time = x
            if time.clock() - fd_time > 20:
                fd.close()
                if (self.fd_dic.get(fd, None) != None):
                    del self.fd_dic[fd]
            else:
                fd_to_close_new.append(x)
        self.fd_to_close = fd_to_close_new

    def attend_client(self, s):
        """
        Attend a client connected to me
        :param s: the connection socket
        :return: True: if is posible close the socket s
                 False: if can not close socket s because a transaction use them
        """
        rqs = self.parse_rqs(s)

        if rqs[0] == "GET":
            try:
                offset = int(rqs[2])  # open file start in the offset
                fo = open(self.path + "/" + rqs[1], "rb")
                fo.seek(offset)  # open a file in a specific position
                size = int(rqs[3])  # size of the porcion of the file to send
                self.create_transaction(fo, s, "send",size, -1, -1)
                return False
            except:
                pass

        if rqs[0] == "HAS":
            try:
                fo = open(self.path + "/" + rqs[1], "rb")
                fo.close()
                size = self.get_len_file(rqs[1])  # send the size of the file
                rps = "%d|%s" % (len(str(size)), str(size))
                s.send(rps.encode())
            except:
                s.send("2|-1".encode())
        return True

    def potencial_location(self, file_name):
        """
        
        :param file_name: 
        :return: 
        """
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
            rqs = "HAS|" + file_name
            rqs = "%d|%s" % (len(rqs), rqs)
            s.send(rqs.encode())
            size = int(self.parse_rqs(s)[0])
            s.close()
        except:
            pass
        return size >= 0

    def Download(self, file_name):
        """

        :param file_name: Name of the file to download
        :return: 0: the download start
                 1: not available file
                 2: dwn fail
                 3: the dwn is in progress now
                 4: the file exits
        """
        try:
            self.download_torrent(file_name)

            if self.dwn_in_progress.__contains__(file_name):
                print(file_name, "download in progress")
                return 3

            if self.files.__contains__(file_name):
                print(file_name, "exits")
                return 4

            location = self.potencial_location(file_name)
            print("location", location)

            if len(location) > 0:
                dwn = Download(self.max_dwn, file_name, self.get_len_file(file_name))
                self.max_dwn += 1
                self.download[dwn.id] = dwn
                dwn.build(location)

                cant_pieces = len(dwn.pieces)
                end = min(cant_pieces,totalP)

                for i in range(0, end):  #start to download the first window of pieces
                    p = dwn.pieces[i]
                    print(file_name + " Piece:" + str(i) + " -->  ", p.attendant, "Size: ", p.size)
                    self.dwn_file_from_peer(file_name, p.attendant, p.offset, p.size, dwn.id, p.id)

                return 0  # the download start
            else:
                print("The file " + file_name + " is not available")
                return 1
        except:
            print("Download " + file_name + " FAILED")
            return 2

    def Pause(self, dwn_id):
        dwn = self.download[dwn_id]
        if dwn.state == "ejecution":
            print("Pause ",dwn.file_name)
            dwn.state = "pause"

            for i in range(len(dwn.pieces)):#deleting pieces incomplets
                p = dwn.pieces[i]
                if not p.finish: #delete the file of this piece
                    p_path = self.path + "/" + dwn.file_name + str(i)
                    try:
                        os.remove(p_path)
                    except:
                        pass

    def Restore(self, dwn_id):
        """
        Restore a paused download
        :param dwn_id: download id
        :return: -1 if not was posible restore
        """
        dwn = self.download[dwn_id]

        dwn.is_fail = False
        print("CANT PIECES FINISH ",dwn.count_finish)
        location = self.potencial_location(dwn.file_name)
        dwn.potential = location
        if len(location):
            print("Start restore")
            dwn.state = "ejecution"

            end = min(len(dwn.pending), totalP)

            for i in range(end):
                p_id = dwn.pending[i]

                print(dwn.file_name, " INTENT RESTORE PIECE ", p_id)
                if not dwn.restart_piece(p_id, False):
                    dwn.is_fail = True
                    print('Fail dwn in restore')
                    return -1
                p = dwn.pieces[p_id]  # mandar a descrgar un window de pieces
                self.dwn_file_from_peer(dwn.file_name, p.attendant, p.offset, p.size, dwn.id, p.id)
            return 0
        return -1

    def Cancel(self, dwn_id):
        dwn = self.download[dwn_id]
        dwn.state = "cancel"
        for i in range(len(dwn.pieces)):  # deleting pieces incomplets
            p = dwn.pieces[i]
            p_path = self.path + "/" + dwn.file_name + str(i)
            try:
                os.remove(p_path)
            except:
                pass

    def dwn_file_from_peer(self, file_name, addr, offset, dwn_size, dwn_id, piece_id):
        s = self.connect_to_peer(addr)

        rqs = "GET|" + file_name + "|" + str(offset) + "|" + str(dwn_size)
        rqs = "%d|%s" % (len(rqs), rqs)
        s.send(rqs.encode())

        fo = open(self.path + "/" + file_name + str(piece_id), "wb")
        self.create_transaction(s, fo, "dwn", dwn_size, dwn_id, piece_id)

    def update_dwn_state(self, dwn, fail = False, finish = False):
        if fail:
            dwn.is_fail = True
            dwn.state = "fail"

            for i in range(len(dwn.pieces)):  # deleting pieces incomplets
                p = dwn.pieces[i]
                if not p.finish:  # delete the file of this piece
                    p_path = self.path + "/" + dwn.file_name + str(i)
                    try:
                        os.remove(p_path)
                    except:
                        pass

        elif finish:
            dwn.state = "finish"

    def reconstruct_file(self, file_name, number_pieces):
        def erase():
            w = open(self.path + "/" + file_name, 'wb')
            for i in range(number_pieces):
                p = self.path + "/" + file_name + str(i)
                try:
                    ri = open(p,"rb")
                    data = ri.read(bufsize)
                    while len(data):
                        w.write(data)
                        data = ri.read(bufsize)
                    ri.close()
                    os.remove(p)
                except:
                    pass
            w.close()
            self.publish(file_name, self.get_len_file(file_name), None)
        Thread(target= erase).start()

    def parse_rqs(self, s):
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

    @verify_dht_conexion
    def set_id(self):
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

    def copy_file_from_directory(self, p_source, file_name):
        p_dest = self.path + "/" + file_name

        def copy():
            # try:
            fi = open(p_source, "rb")
            fo = open(p_dest, "wb")
            d = fi.read(bufsize)
            size = 0
            while d:
                fo.write(d)
                size += len(d)
                d = fi.read(bufsize)

            fi.close()
            fo.close()

            dwn = Download(-1,file_name, size)
            dwn.partition()
            metadata = self.torrent_metadata(dwn)
            self.create_torrent( metadata)
            self.publish(file_name, size, metadata)  #publish a file location
            # except:
            #     print("failed open file in copy from a directory")
            os.remove(p_source)
        self.pub.append(Thread(target=copy, args=()))
        self.pub[-1].start()

    def download_torrent(self, file_name):
        t_name = file_name + ".torrent"
        t = self.get_torrent(t_name)
        self.create_torrent(t)
        print("Client " + str(self.c_id) + " download " + file_name + ".torrent")

    def torrent_metadata(self, dwn):
        t = {}
        t["file"] = dwn.file_name
        t["size"] = dwn.size
        count_pieces = len(dwn.pieces)
        t["count_piece"] = count_pieces
        print(dwn.file_name + ".torrent metadata count pieces", count_pieces)

        for i in range(count_pieces):
            p = dwn.pieces[i]
            try:
                f = open(self.path + "/" + dwn.file_name, "rb")
                f.seek(p.offset)
                p_data = f.read(p.size)

                t["len_piece|" + str(p.id)] = p.size
                t["hash_piece|" + str(p.id)] = hashb(p_data)
            except:
                print("failed when intent open file in Torrent metadata")
        return t

    @verify_dht_conexion
    def get_torrent(self, torrent_name):
        t = self.comunicator.get_torrent(torrent_name)
        return t

    def create_torrent(self,metadata):
        file_name = metadata["file"]
        path = self.path + "/" + file_name
        torrent_parser.create_torrent_file(f'{path}.torrent', metadata)

    def parse_torrent(self, file_name):
        path = self.path + "/" +file_name + ".torrent"
        t = torrent_parser.parse_torrent_file(path)
        return t

    def check_piece_with_torrent(self, p_id, p_data, p_size, file_name):
        t = self.parse_torrent(file_name)
        p_hash = hashb(p_data)
        if p_size != t["len_piece|" + str(p_id)]:
            return False
        else:
            return p_hash == t["hash_piece|" + str(p_id)]

    def torrent_exists(self, file_name):
        try:
            t = open(self.path + "/" + file_name  + ".torrent" , "r")
        except:
            return False
        return True

    @verify_dht_conexion
    def get_len_file(self, file_name):
        return self.comunicator.get_len_file(file_name)

    def read_len_file(self, path, file_name):
        try:
            f = open(path + "/" + file_name, "rb")
            d = f.read(bufsize)
            size = 0
            while d:
                size += len(d)
                d = f.read(bufsize)
            return size
        except:
            return -1

    @verify_dht_conexion
    def publish(self, file_name, size, torrent):
        self.files.append(file_name)
        self.comunicator.publish(file_name, self.c_id, size, torrent)

    @verify_dht_conexion
    def get_file_location(self, file):
        nodes = self.comunicator.get_location(file)
        return nodes

    @verify_dht_conexion
    def see_files(self):
        all = self.comunicator.all_files()
        return all

    def load_my_files(self):
        extension = [".torrent", ".json" , "id"]
        files = [f for f in os.listdir(self.path) if not any(f.endswith(ext) for ext in extension)]
        return files

    def torrent_exists(self, file_name):
        try:
            t = open(self.path + "/" + file_name  + ".torrent" , "r")
        except:
            return False
        return True


def main():
    print("client.py")

    l = [1,2,3,4,5]
    l.remove(4)
    print(l)




if __name__ == "__main__":
    main()
