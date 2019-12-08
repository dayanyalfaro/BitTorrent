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
c0 = Client( "192.168.43.253", 8001, p + "0", ("192.168.43.253", 7001))
time.sleep(1)

c0.copy_file_from_directory("./file.pdf", "file.pdf")



input()
#
# time.sleep(1)
#
c0.Download("peli.avi")
#
#
#
