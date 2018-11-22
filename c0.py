from client import Client
import os
import time

p = "./Storage/Client"
try:
    os.mkdir("./Storage")
except:
    pass

c0 = Client("localhost", 8000, "localhost", 8888, p + "0", ("localhost", 9000))
time.sleep(1)
# c0.copy_file_from_directory("./foto.jpg", "foto.jpg")
# c0.copy_file_from_directory("./foto2.png", "foto2.png")
# c0.copy_file_from_directory("./dht.py", "dht.py")
c0.copy_file_from_directory("./tesis.pdf", "tesis.pdf")