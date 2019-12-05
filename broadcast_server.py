import socket
import threading
import time

def broadcast_server(ip,port):
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST, 1)

    server.bind(('',37020))
    is_conecting = []
    while True:
        data, addr = server.recvfrom(1024)
        if int(data.decode()) > 0 and int(data.decode()) != port:# and ip != addr[0]:
            print(data.decode())
            if not is_conecting.__contains__(int(data.decode())):
                is_conecting.append(int(data.decode()))
                th = threading.Thread(target = broadcast_server_auxiliar,args =(addr[0],data.decode(),ip,port,))
                th.start()

def broadcast_server_auxiliar(ip,port,my_ip,my_port):
    s = socket.socket(type=socket.SOCK_STREAM)
    try:
        s.connect((ip,int(port) + 1000))
        answer = s.recv(4)
        print('conection from ' + str(int(port) + 1000))
        pack = str((my_ip,my_port))
        s.send(pack.encode())
        answer = s.recv(4)
        s.close()
    except:
        s.close()
