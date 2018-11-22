from client import Client
import os
import time


p = "./Storage/Client"

c1 = Client("localhost", 8001, "localhost", 8888, p + "1", ("localhost", 9001))
time.sleep(4)
f = "foto2.png"
f2 = "dht.py"

# c1.copy_file_from_directory("./foto2.png", "foto2.png")
c1.copy_file_from_directory("./tesis.pdf", "tesis.pdf")
# c1.copy_file_from_directory("./dht.py", "dht.py")
# c1.Download("tesis.pdf")
