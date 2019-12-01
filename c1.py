from client import Client
import os
import time

p = "./Storage/Client"
try:
    os.mkdir("./Storage")
except:
    pass


c1 = Client("localhost", 8001, 'localhost', 8888, p + "1", ('localhost', 9001))
time.sleep(1)
f = "foto2.png"
f2 = "dht.py"

# c1.copy_file_from_directory("./foto2.png", "foto2.png")
# c1.copy_file_from_directory("./tesis.pdf", "tesis.pdf")
# c1.copy_file_from_directory("./dht.py", "dht.py")
# c1.copy_file_from_directory("./hello", "hello")
time.sleep(3)
c1.download_torrent("dht.py")
c1.Download("dht.py")
time.sleep(3)
c1.download_torrent("hello")
c1.Download("hello")
time.sleep(1)
c1.download_torrent("foto2.png")
c1.Download("foto2.png")
print(c1.Download("hello"))