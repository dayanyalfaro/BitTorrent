from client import Client
import os
import time


p = "./Storage/Client"

c2 = Client("localhost", 8002, "localhost", 8888, p + "2", ("localhost", 9002))
time.sleep(4)
f = "tesis.pdf"
f2 = "dht.py"

c2.copy_file_from_directory("./dht.py", "dht.py")
c2.copy_file_from_directory("./tesis.pdf", "tesis.pdf")
# c2.Download("dht.py")
# c2.Download("tesis.pdf")
