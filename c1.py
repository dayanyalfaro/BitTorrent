from client import Client
import os
import time

p = "./Storage/Client"
try:
    os.mkdir("./Storage")
except:
    pass


c1 = Client( "127.0.0.1", 8888, p + "1", ("127.0.0.1", 9001))
time.sleep(1)
f = "foto2.png"
f2 = "dht.py"

# c1.copy_file_from_directory("./foto2.png", "foto2.png")

c1.Download("pulp.mp4")
# time.sleep(1)
#
# c1.Download("dht.py")
# time.sleep(1)
#
# c1.Download("tools.py")
# time.sleep(2)
c1.Download("foto2.png")

#
time.sleep(3)
c1.Cancel(0)

# c1.Pause(0)
# #
# time.sleep(2)
# # # print(c1.download)
# # #
# # # input()
# # #
# print(c1.Restore(0))
