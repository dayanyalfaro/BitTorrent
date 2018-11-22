from client import Client
import os
import time


p = "./Storage/Client"

c3 = Client("localhost", 8003, "localhost", 8888, p + "3", ("localhost", 9003))
time.sleep(4)
f = "tesis.pdf"
f2 = "dht.py"

# c3.Download("dht.py")
time.sleep(4)
c3.Download("tesis.pdf")
