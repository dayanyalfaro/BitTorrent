from client import Client
import os
import time


p = "./Storage/Client"

c3 = Client("localhost", 8003, "127.0.0.1", 8888, p + "3", ("localhost", 9003))
time.sleep(4)
f = "tesis.pdf"
f2 = "dht.py"


# c3.download_torrent("dht.py")
# c3.Download("dht.py")
# time.sleep(1)
# c3.download_torrent("matcom.png")
# c3.Download("matcom.png")
time.sleep(1)
c3.download_torrent("peli.avi")
c3.Download("peli.avi")
