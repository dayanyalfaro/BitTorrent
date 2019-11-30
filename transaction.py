from tools import *
import math as m
import random as rd


class Download(object):
    def __init__(self, id, file_name, size):
        self.id = id
        self.file_name = file_name
        self.size = size
        self.pieces = {}
        self.count_finish = 0
        self.potential = []
        self.is_fail = False
        #TODO pause dwn
        self.state = "ejecution"  #['finished', 'canceled', 'paused', 'restore', 'ejecution']

    def partition(self):
        """
        Segmentate the file in pieces
        """
        cantPieces = m.floor(m.log2(self.size))
        step = m.floor(self.size/cantPieces)# cantPieces constant m.floor(self.size / totalP)  # m.floor(self.size ** 0.5)
        if step == 0:
            step = self.size
        print("STEP", step, "SIZE", self.size)
        piece_id = 0
        actual_offset = 0
        while step <= self.size - actual_offset:
            self.pieces[piece_id] = Piece(piece_id, actual_offset, step)
            piece_id += 1
            actual_offset += step
        print("ACTUAL OFFSET", actual_offset)
        if actual_offset != self.size:
            self.pieces[piece_id] = Piece(
                piece_id, actual_offset, self.size - actual_offset
            )

    def distribute(self, pot_location):
        actual_n = 0

        for k in self.pieces.keys():
            self.pieces[k].attendant = pot_location[actual_n]
            actual_n = (actual_n + 1) % len(pot_location)

        self.potential = pot_location

    def build(self, pot_location):
        self.partition()
        self.distribute(pot_location)

    def restart_piece(self, id_piece):
        broken_node = self.pieces[id_piece].attendant
        if broken_node in self.potential:
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

    def write(self):
        # try:
        # TODO : Poner try para captar la excepcion, la escritura fallo
        if self.type == "dwn":
            self.fo.write(self.data)
            self.data_dwn += self.data
        if self.type == "send":
            self.fo.send(self.data)
        self.is_load = False
        self.actual_copy += len(self.data)
        if self.actual_copy >= self.size:
            self.finish = True
            self.fi.close()
            if self.type == "dwn":
                self.fo.close()
        elif len(self.data) == 0: # TODO: Parche aqui
            self.is_fail = True




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
            self.fi.close()
            self.fo.close()
            print("fail read transaction")

    def __str__(self):
        return "%s -> %s, [%s], (%s), t: %s"%(str(self.fi), str(self.fo), str(self.is_fail), str(self.finish), str(self.type))

# d = Download("aa", 21)
# d.partition()
# d.distribute([11, 12, 13, 14, 15])
# for k in d.pieces.values():
#     print(k.id, k.offset, k.size, k.attendant)
