from client import Client
import os
from transaction import *
import time

p = "./Storage/Client"
try:
    os.mkdir("./Storage")
except:
    pass
#
c0 = Client("localhost", 8000, "192.168.43.124", 8888, p + "0", ("192.168.43.124", 9000))
time.sleep(1)
c0.copy_file_from_directory("./dht.py", "dht.py")
# # c0.copy_file_from_directory("./foto2.png", "foto2.png")
#
# # d = Download(-1,"hello", 10)
# # d.partition()
# # t =c0.torrent_metadata(d)
# # print(t)
# # c0.create_torrent("hello", t)
# # p = c0.parse_torrent("hello")
# # print("Torrent parse" ,p)
time.sleep(2)
c0.copy_file_from_directory("./matcom.png", "matcom.png")
# # # c0.copy_file_from_directory("./hello", "hello")
time.sleep(2)
c0.copy_file_from_directory("./peli.avi", "peli.avi")





