import os
import socket
import time
import torrent_parser
import json
import re
from select import select
from threading import Thread

from middleware import Comunicator
from tools import *
from transaction import Transaction, Download


class Client(object):
    def __init__(self, ip, port, dht_ip, dht_port, path, addr_listen):
        self.c_id = None
        self.ip = ip
        self.port = port
        self.path = path
        self.comunicator = Comunicator(addr_listen, dht_ip, dht_port)
        self.download = {}
        self.history = None   #TODO history of downloads
        self.max_dwn = 0
        self.pending = []
        self.fd_dic = {}
        self.pub = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addr_listen = addr_listen

        try:
            os.mkdir(self.path)
        except:
            print("no open Storage")

        self.set_id()
        self.update_history()
        self.files = self.load_my_files()

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

            rfd, wfd, efd = select(inputs, outputs, inputs + outputs, 2)

            for s in rfd:
                if s == self.sock:
                    conn, addr = self.sock.accept()
                    pend_to_attend.append(conn)
                elif s in pend_to_attend:
                    self.attend_client(s)
                    pend_to_attend.remove(s)
                else:
                    t = self.fd_dic[s]

                    if t.type == "dwn":
                        dwn = self.download[t.dwn_id]
                        if dwn.state == "pause" :  #si la transaccion es de una descarga pausada => ya no se ejecuta mas
                            # t.fi.close()
                            # t.fo.close()
                            self.pending.remove(t)
                            self.update_history()
                            continue

                        t.read()
                        if t.is_fail:
                            restart = dwn.restart_piece(t.piece_id)
                            print("Intent restart", restart)

                            if not restart:
                                print("Download of " + dwn.file_name + "FAILED")
                                dwn.is_fail = True
                                dwn.state = "fail"
                                self.update_history()
                            else: #si se pudo arreglar => se encargara otro nodo de ese piece
                                p = dwn.pieces[t.piece_id]
                                self.dwn_file_from_peer(dwn.file_name, p.attendant,p.offset,p.size,dwn.id, p.id)
                    else:
                        t.read()

            for s in wfd:

                t = self.fd_dic[s]

                if t.type == 'dwn':
                    dwn = self.download[t.dwn_id]
                    if dwn.state == "pause":
                        # t.fi.close()
                        # t.fo.close() #este si
                        self.pending.remove(t)
                        self.update_history()
                        continue

                    t.write()

                    if t.finish:
                        print("FINISH Piece:", t.piece_id)
                        check = self.check_piece_with_torrent(t.piece_id,t.data_dwn,t.size, dwn.file_name)#check if the piece is correct
                        if check:
                            dwn.success_piece(t.piece_id)
                            print(dwn.file_name, "SUCCESS Piece:", t.piece_id)
                            if dwn.is_finish():  # if all pieces done ==> publish file
                                print(dwn.file_name, " Download finished")
                                dwn.state = "finish"
                                self.update_history()
                                self.reconstruct_file(dwn.file_name, len(dwn.pieces))
                        else:
                            print("Incorrect Piece was download")
                            os.remove(self.path + "/" + dwn.file_name + str(t.piece_id))
                            restart = dwn.restart_piece(t.piece_id)

                            if not restart:
                                print("Download of " + dwn.file_name + "FAILED")
                                dwn.is_fail = True
                                dwn.state = "fail"
                                self.update_history()
                            else:
                                p = dwn.pieces[t.piece_id]
                                self.dwn_file_from_peer(dwn.file_name, p.attendant, p.offset, p.size, dwn.id, p.id)
                    elif t.is_fail:
                        restart = dwn.restart_piece(t.piece_id)
                        print("Intent restart", restart)
                        if not restart:
                            print("Download of " + dwn.file_name + "FAILED")
                            dwn.is_fail = True
                            dwn.state = "fail"
                            self.update_history()
                        else:
                            p = dwn.pieces[t.piece_id]
                            self.dwn_file_from_peer(dwn.file_name, p.attendant,p.offset,p.size,dwn.id, p.id)
                else:
                    t.write()


            self.pending = [i for i in self.pending if not i.finish and not i.is_fail]
            #TODO delete transaction from fd_dic


            # for i in self.pending:
            #     print (i)
            # print(len(self.pending))
            # time.sleep(0.5)

    def attend_client(self, s):
        rqs = self.parse_rqs(s)

        if rqs[0] == "GET":
            try:
                offset = int(rqs[2])  # open file start in the offset
                fo = open(self.path + "/" + rqs[1], "rb")
                fo.seek(offset)  # open a file in a specific position
                size = int(rqs[3])  # size of the porcion of the file to send
                self.create_transaction(fo, s, "send",size, -1, -1)
            except:
                pass
        if rqs[0] == "HAS":
            try:
                fo = open(self.path + "/" + rqs[1], "rb")
                size = self.get_len_file(rqs[1])  # send the size of the file
                rps = "%d|%s" % (len(str(size)), str(size))
                s.send(rps.encode())
            except:
                s.send("2|-1".encode())

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
            rqs = "HAS|" + file_name
            rqs = "%d|%s" % (len(rqs), rqs)
            s.send(rqs.encode())
            size = int(self.parse_rqs(s)[0])
        except:
            pass
        return size >= 0

    def Download(self, file_name):
        """
        
        :param file_name: Name of the file to download
        :return: 0: is posible download file
                 1: if the .torrent is needed
                 2: if the file exist
                 3: not available file
        """
        try:
            t = open(self.path + "/" + file_name  + ".torrent" , "r")
        except:
            print("You need download " + file_name + ".torrent before download file")
            return 1

        try:
            f = open(self.path + "/" + file_name , "r")
            print("The file " + file_name + " exist" )
            return 2
        except:
            location = self.potencial_location(file_name)
            print("location", location)

            if len(location) > 0:
                dwn = Download(self.max_dwn, file_name, self.get_len_file(file_name))
                self.max_dwn += 1
                self.download[dwn.id] = dwn
                dwn.build(location)

                for i in range(len(dwn.pieces)):
                    p = dwn.pieces[i]
                    print("Piece:" + str(i) + " -->  ", p.attendant, "Size: ", p.size)
                    self.dwn_file_from_peer(file_name, p.attendant, p.offset, p.size, dwn.id, p.id)
                return 0  #the download start
            else:
                print("The file " + file_name + " is not available")
                return 3

    def Pause(self, dwn_id):
        print("max_down", self.max_dwn)
        print("len", len(self.download))
        dwn = self.download[dwn_id]
        if dwn.state == "ejecution":
            print("Pause ",dwn.file_name)
            dwn.state = "pause"

            #TODO: Aqui podria eliminar los fd del pending relacionados con la dwn
            # self.pending = [i for i in self.pending if i.dwn_id != dwn_id] #me dio error en start_listen

            #deleting pieces incomplets
            for i in range(len(dwn.pieces)):
                p = dwn.pieces[i]
                if not p.finish: #delete the file of this piece
                    p_path = self.path + "/" + dwn.file_name + str(i)
                    os.remove(p_path)

    def Restore(self, dwn_id):
        """
        Restore a paused download
        :param dwn_id: download id
        :return: -1 if not was posible restore
        """
        dwn = self.download[dwn_id]
        if dwn.state == "pause":
            print("CANT PIECES FINISH ",dwn.count_finish)
            location = self.potencial_location(dwn.file_name)
            if len(location):
                print("Start restore")
                print("Pending", len(self.pending))
                dwn.state = "ejecution"
                for i in range(len(dwn.pieces)):
                    p = dwn.pieces[i]
                    if not p.finish:  # delete the file of this piece
                        print(dwn.file_name, " RESTORE PIECE ", i)
                        dwn.potential = location
                        dwn.restart_piece(i)
                        p = dwn.pieces[i]

                        self.dwn_file_from_peer(dwn.file_name,p.attendant, p.offset, dwn.size, dwn_id, p.id)
                        l = [i.dwn_id for i in self.pending]
                        print(l)

                return 0
            else:
                return -1

    def Cancel(self):
        pass

    def dwn_file_from_peer(self, file_name, addr, offset, dwn_size, dwn_id, piece_id):
        s = self.connect_to_peer(addr)

        rqs = "GET|" + file_name + "|" + str(offset) + "|" + str(dwn_size)
        rqs = "%d|%s" % (len(rqs), rqs)
        s.send(rqs.encode())

        fo = open(self.path + "/" + file_name + str(piece_id), "wb")
        self.create_transaction(s, fo, "dwn", dwn_size, dwn_id, piece_id)

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

    def publish(self, file_name, size, torrent):
        self.files.append(file_name)
        self.comunicator.publish(file_name, self.c_id, size, torrent)

    def get_file_location(self, file):
        nodes = self.comunicator.get_location(file)
        return nodes

    def see_files(self):
        all = self.comunicator.all_files()
        all = [f for f in all if f not in self.files]
        return all

    def update_history(self):
        d = {}
        start = 0
        if histsize < self.max_dwn:
            start = self.max_dwn - histsize
        d["range"] = {"first": str(start), "last":str(self.max_dwn - 1)} #TODO arreglar el last
        for k in range(start, self.max_dwn):
            dwn = self.download[k]
            data = {"file":dwn.file_name, "size": str(dwn.size), "copy":str(dwn.actual_copy), "state": dwn.state}
            d[str(k)] = data

        with open(self.path + "/history.json", "w") as wfd:
            json.dump(d, wfd)

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



if __name__ == "__main__":
    main()