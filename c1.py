from client import Client
import os
import time


p = "./Storage/Client"

c1 = Client("localhost", 8001, "127.0.0.1", 8888, p + "1", ("127.0.0.1", 9001))
time.sleep(1)
f = "foto2.png"
f2 = "dht.py"

# c1.copy_file_from_directory("./foto2.png", "foto2.png")
# c1.copy_file_from_directory("./tesis.pdf", "tesis.pdf")
# c1.copy_file_from_directory("./dht.py", "dht.py")
# c1.copy_file_from_directory("./hello", "hello")
# time.sleep(4)
c1.download_torrent("dht.py")
c1.Download("dht.py")
time.sleep(1)
c1.download_torrent("matcom.png")
c1.Download("matcom.png")
time.sleep(1)
c1.download_torrent("peli.avi")
c1.Download("peli.avi")