from client import Client
import os
import time

p = "./Storage/Client"
try:
    os.mkdir("./Storage")
except:
    pass


c1 = Client( "192.168.43.253", 8000, p + "1", ("192.168.43.253", 9001))
time.sleep(1)
f = "foto2.png"
f2 = "dht.py"

c1.copy_file_from_directory("./file.pdf", "file.pdf")

# time.sleep(1)
#
# c1.Download("peli.avi")