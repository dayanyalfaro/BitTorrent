from client import Client
import os
from transaction import *
import time

p = "./Storage/Client"
try:
    os.mkdir("./Storage")
except:
    pass

c0 = Client("localhost", 8000, "localhost", 8888, p + "0", ("localhost", 9000))
time.sleep(1)
c0.copy_file_from_directory("./dht.py", "dht.py")
c0.copy_file_from_directory("./foto2.png", "foto2.png")
c0.copy_file_from_directory("./dht.py", "dht.py")

# d = Download(-1,"hello", 10)
# d.partition()
# t =c0.torrent_metadata(d)
# print(t)
# c0.create_torrent("hello", t)
# p = c0.parse_torrent("hello")
# print("Torrent parse" ,p)
# c0.copy_file_from_directory("./kramer.avi", "kramer.avi")
c0.copy_file_from_directory("./hello", "hello")





