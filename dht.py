import Pyro4

from tools import start_service


@Pyro4.expose
class DHT(object):
    def __init__(self):
        self.d = {}

    def set(self, k, v):
        self.d[k] = v
        print(self.d)
        print("\n")
        print("****************************************************************")

    def get(self, k):
        return self.d.get(k)


def main():
    print("hello")
    d = DHT()
    d.d["#maxclient"] = 0
    d.d["#allfiles"] = []
    print(d.d)

    ip = "localhost"  # change
    port = 8888
    start_service(d, ip, port)


main()