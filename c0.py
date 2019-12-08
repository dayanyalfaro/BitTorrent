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
c0 = Client( "10.0.0.1", 8001, p + "0", ("10.0.0.1", 7001))
time.sleep(1)

c0.copy_file_from_directory("./file2.mkv", "file2.mkv")



input()
#
# time.sleep(1)
#
c0.Download("video2.mpg")
#
#
#
