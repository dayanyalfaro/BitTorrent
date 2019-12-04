from client import Client
import os
from transaction import *
import time

p = "./Storage/Client"
try:
    os.mkdir("./Storage")
except:
    pass

time.sleep(1)
#
c0 = Client( "127.0.0.1", 8888, p + "0", ("127.0.0.1", 9000))
time.sleep(1)
# c0.copy_file_from_directory("./dht.py", "dht.py")
# # time.sleep(1)
# # c0.copy_file_from_directory("./tesis.pdf", "tesis.pdf")
# # time.sleep(1)
# c0.copy_file_from_directory("./chord.py", "chord.py")
# # time.sleep(1)
# c0.copy_file_from_directory("./kramer.avi", "kramer.avi")
# # time.sleep(2)
c0.copy_file_from_directory("./foto2.png", "foto2.png")



