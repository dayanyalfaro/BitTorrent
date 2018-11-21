import Pyro4
import os
from tools import *


class Comunicator(object):
    def __init__(self, addr_listen, dht_ip, dht_port):
        self.dht_ip = dht_ip
        self.dht_port = dht_port
        self.addr_listen = addr_listen

    def update_dht(self, d_ip, d_port):
        """
            update the DHT address
        """
        self.dht_ip = d_ip
        self.dht_port = d_port

    def update_client(self, addr):
        """
            update the Client address
        """
        self.addr_listen = addr

    def get_id(self):
        dht = get_remote_node(self.dht_ip, self.dht_port)
        id = dht.get(maxclient)
        dht.set(maxclient, id + 1)
        dht.set(idclient + str(id), (self.addr_listen))
        return id

    def update_idclient(self, id, addr):
        dht = get_remote_node(self.dht_ip, self.dht_port)
        dht.set(idclient + str(id), addr)

    def publish(self, torrent, c_id, size):  # ver lo del id del cliente
        """
            Publish a torrent in the tracker
        """
        dht = get_remote_node(self.dht_ip, self.dht_port)
        v = dht.get(torrent)

        if v == None:
            dht.set(torrent, [c_id])
            all = dht.get(allfiles)
            all.append(torrent)
            dht.set(allfiles, all)
            k = sizefile + "|" + torrent
            dht.set(k, size)
        else:
            if not v.__contains__(c_id):
                v.append(c_id)
                dht.set(torrent, v)
        print("client ", c_id, "published file ", torrent)

    def all_files(self):
        """
            List all files availables
        """
        dht = get_remote_node(self.dht_ip, self.dht_port)
        files = dht.get(allfiles)
        return files

    def get_len_file(self, file_name):
        dht = get_remote_node(self.dht_ip, self.dht_port)
        l = dht.get(sizefile + "|" + file_name)
        return l

    def get_location(self, file_name):  # asumiendo q la llave es el nombre del file
        dht = get_remote_node(self.dht_ip, self.dht_port)
        nodes_ids = dht.get(file_name)

        addrs = []
        for n in nodes_ids:
            d = dht.get(idclient + str(n))
            addrs.append(d)
        return addrs

    def get_torrent(self):  # return the torrent file
        pass


def main():
    path = "/home/dalianys/Escritorio/Distribuidos/BitTorrent/BitTorrent/Storage"
    f = open(path + "txt", "w")
    # f.write(str(4))
    try:
        os.mkdir(path)
    except:
        print("can not create directory")


if __name__ == "__main__":
    main()

