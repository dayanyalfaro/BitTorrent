from client import Client
import os
import time


p = "./Storage/Client"

c2 = Client("localhost", 8002, "192.168.43.124", 8888, p + "2", ("192.168.43.124", 9002))
time.sleep(4)
f = "tesis.pdf"
f2 = "dht.py"

# c2.copy_file_from_directory("./dht.py", "dht.py")
# c2.copy_file_from_directory("./tesis.pdf", "tesis.pdf")

c2.download_torrent("dht.py")
c2.Download("dht.py")
time.sleep(1)
c2.download_torrent("matcom.png")
c2.Download("matcom.png")
time.sleep(1)
c2.download_torrent("peli.avi")
c2.Download("peli.avi")
