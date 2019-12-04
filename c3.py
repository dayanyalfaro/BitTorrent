from client import Client
import os
import time


p = "./Storage/Client"

c3 = Client( "127.0.0.1", 8888, p + "3", ("127.0.0.1", 9003))
time.sleep(4)
f = "tesis.pdf"
f2 = "dht.py"

#
# c3.Download("dht.py")
# time.sleep(1)
c3.Download("foto2.png")
# time.sleep(1)
#
# c3.Download("tools.py")
