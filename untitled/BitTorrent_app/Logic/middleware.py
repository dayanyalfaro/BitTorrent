
from BitTorrent_app.Logic.tools import *


class Comunicator(object):
    def __init__(self, addr_listen, dht_ip, dht_port):
        self.dht_ip = dht_ip
        self.dht_port = dht_port
        self.addr_listen = addr_listen

    def get_alternative_nodes(self):
        dht_nodes = []
        try:
            remote = get_remote_node(self.dht_ip,self.dht_port)
            successors = remote.successors
            dht_nodes = [ suc['id'].split(':') for suc in successors]
        except:
            pass
        return dht_nodes

    def update_dht(self, d_ip, d_port):
        """
            update the DHT address
        """
        self.dht_ip = d_ip
        self.dht_port = d_port

    def get_id(self):
        dht = get_remote_node(self.dht_ip, self.dht_port)
        id = dht.get(get_hash(maxclient))
        dht.set(get_hash(maxclient), id + 1)
        dht.set(get_hash(idclient + str(id)), (self.addr_listen))
        return id

    def update_idclient(self, id, addr):
        dht = get_remote_node(self.dht_ip, self.dht_port)
        dht.set(get_hash(idclient + str(id)), addr)

    def publish(self, file_name, c_id, size, torrent):  # ver lo del id del cliente
        """
            Publish a torrent in the tracker
        """
        dht = get_remote_node(self.dht_ip, self.dht_port)
        v = dht.get(get_hash(file_name))

        if v == None:
            dht.set(get_hash(file_name), [c_id])
            cantstep = dht.get(get_hash(maxstep))
            print("cantstep", cantstep)
            l  = len(dht.get(get_hash(filestep + "|" + str(cantstep))))
            if l == lenstep: #create new step
                print("full step")
                dht.set(get_hash(maxstep), cantstep + 1)
                dht.set(get_hash(filestep + "|" + str(cantstep + 1)), [file_name])
            else:
                all = dht.get(get_hash(filestep + "|" + str(cantstep)))
                all.append(file_name)
                dht.set(get_hash(filestep + "|" + str(cantstep)), all)
            k = sizefile + "|" + file_name
            dht.set(get_hash(k), size)
            dht.set(get_hash(file_name + ".torrent"), torrent) #first time to publish this .torrent
        else:
            if not v.__contains__(c_id):
                v.append(c_id)
                dht.set(get_hash(file_name), v)
        print("client ", c_id, "published file ", file_name)


    def get_files(self, step):
        """
            List all files availables
        """
        dht = get_remote_node(self.dht_ip, self.dht_port)
        files = dht.get(get_hash(filestep + "|" + str(step)))
        return files

    def all_files(self):
        files = []
        dht = get_remote_node(self.dht_ip, self.dht_port)
        cantstep = dht.get(get_hash(maxstep))

        for i in range(cantstep + 1):
            files += self.get_files(i)

        return files


    def get_len_file(self, file_name):
        dht = get_remote_node(self.dht_ip, self.dht_port)
        l = dht.get(get_hash(sizefile + "|" + file_name ))
        return l

    def get_location(self, file_name):  # asumiendo q la llave es el nombre del file
        dht = get_remote_node(self.dht_ip, self.dht_port)
        nodes_ids = dht.get(get_hash(file_name))

        addrs = []
        for n in nodes_ids:
            d = dht.get(get_hash(idclient + str(n)))
            addrs.append(d)
        return addrs

    def get_torrent(self, torrent_name):
        dht = get_remote_node(self.dht_ip, self.dht_port)
        t = dht.get(get_hash(torrent_name))
        return t


def main():
    print("middleware")


if __name__ == "__main__":
    main()