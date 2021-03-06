from BitTorrent_app.Logic.tools import *
import math as m
import random as rd
import time

MB = 1024*1024
GB = 1024*1024*1024
max_cant_pieces = 500

class Download(object):
    def __init__(self, id, file_name, size):
        self.id = id
        self.file_name = file_name
        self.size = size
        self.pieces = {}
        self.pending = []
        self.count_finish = 0
        self.actual_copy = 0
        self.potential = []
        self.is_fail = False
        self.state = "ejecution"

    def define_piece_length(self):
        if self.size <= 50*MB: #size file lower 50 mg
            return MB
        elif 50*MB < self.size < GB:
            return 2*MB
        elif m.ceil(self.size/4*MB) < max_cant_pieces:
            return 4*MB#ver si puedo con 4megas
        else:
            p_size = m.ceil(self.size/max_cant_pieces)
            return p_size

    def partition(self):
        """
        Segmentate the file in pieces
        """
        step =  self.define_piece_length()

        if step == 0 or step > self.size:
            step = self.size
        piece_id = 0
        actual_offset = 0
        while step <= self.size - actual_offset:
            self.pieces[piece_id] = Piece(piece_id, actual_offset, step)
            self.pending.append(piece_id)
            piece_id += 1
            actual_offset += step

        if actual_offset != self.size:
            self.pending.append(piece_id)
            self.pieces[piece_id] = Piece(
                piece_id, actual_offset, self.size - actual_offset
            )

        print(self.file_name, "CANTIDAD PIECES:", len(self.pieces), "PIECE SIZE:", step, "FILE SIZE:" , self.size)

    def distribute(self, pot_location):
        actual_n = 0

        for k in self.pieces.keys():
            self.pieces[k].attendant = pot_location[actual_n]
            actual_n = (actual_n + 1) % len(pot_location)

        self.potential = pot_location

    def build(self, pot_location):
        self.partition()
        self.distribute(pot_location)

    def restart_piece(self, id_piece, remove = True):
        broken_node = self.pieces[id_piece].attendant
        if remove and broken_node in self.potential:
            self.potential.remove(broken_node)
        if len(self.potential) > 0:
            r = rd.randint(0, len(self.potential) - 1)
            self.pieces[id_piece].attendant = self.potential[r]
            return True
        else:
            return False

    def success_piece(self, id_piece):
        self.pieces[id_piece].finish = True
        self.count_finish += 1
        self.actual_copy += self.pieces[id_piece].size
        self.pending.remove(id_piece)
        new_piece_to_dwn = id_piece + totalP
        if new_piece_to_dwn < len(self.pieces):
            return self.pieces[new_piece_to_dwn]
        else:
            return -1

    def is_finish(self):
        return (self.count_finish == len(self.pieces)) and (self.count_finish != 0)


class Piece(object):
    def __init__(self, id, offset, size):
        self.id = id
        self.offset = offset
        self.size = size
        self.attendant = None
        self.finish = False


class Transaction(object):
    def __init__(self, fi, fo, type_t, size, dwn_id, piece_id):
        self.fi = fi
        self.fo = fo
        self.type = type_t
        self.size = size
        self.actual_copy = 0
        self.data = None
        self.data_dwn = "".encode()
        self.is_load = False
        self.is_fail = False
        self.finish = False
        self.dwn_id = dwn_id
        self.piece_id = piece_id
        self.time = time.clock()
        self.timeout_error = False

    def write(self):
        try:
            le = len(self.data)
            if self.type == "dwn":
                self.fo.write(self.data)
                self.data_dwn += self.data
                self.is_load = False
            if self.type == "send":
                le = self.fo.send(self.data)
                if(le == len(self.data)):
                    self.is_load = False
                else:
                    self.data = self.data[le:]

            self.actual_copy += le
            if self.actual_copy >= self.size:
                self.finish = True
                self.fi.close()
                if self.type == "dwn":
                    self.fo.close()
            elif le == 0:
                self.is_fail = True
                self.close()
            self.time = time.clock()
        except:
            self.is_fail = True
            self.close()
            print ("Fail transaccion in write", self.dwn_id, self.piece_id)

    def read(self):
        bf = min(bufsize, self.size - self.actual_copy)
        try:
            if self.type == "dwn":
                self.data = self.fi.recv(bf)
            if self.type == "send":
                self.data = self.fi.read(bf)

            self.is_load = True
        except:
            self.is_fail = True
            self.close()
            print("fail read transaction")
        self.time = time.clock()

    def close(self):
        self.fi.close()
        self.fo.close()

    def validate_timeout(self, time_out):
        if(time.clock() - self.time > time_out):
            self.is_fail = True
            if self.type == "dwn":
                self.timeout_error = True
            self.close()
            print ("Fail transaction because timeout:", time_out)
            # TODO hacer prueba de socket aqui un poco mas fuertes.

    def __str__(self):
        return "%s -> %s, [%s], (%s), t: %s"%(str(self.fi), str(self.fo), str(self.is_fail), str(self.finish), str(self.type))


