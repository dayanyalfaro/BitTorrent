import socket
import threading
import time

def broadcast_client(ip,port):
    client = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

    client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    client.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST, 1)
    message = str(port)
    lista = []
    th = threading.Thread(target = broadcast_client_auxiliar,args = (ip,port + 1000,lista,))
    th.start()
    while True:
        client.sendto(message.encode(),('255.255.255.255',37020))
        time.sleep(2)
        if len(lista) > 0:
            break
    print(lista[0])
    return lista[0]

def broadcast_client_auxiliar(ip,port,lista):
    s = socket.socket(type=socket.SOCK_STREAM)
    s.bind((ip,port))
    s.listen(1)
    sc , adr = s.accept()
    sc.send(b'done')
    pack = sc.recv(1024)
    sc.send(b'done')
    pack = pack.decode()
    pack = pack[1:-1]
    pack = pack.split(',')
    l = pack[0].split("'")
    pack = (l[1],int(pack[1]))
    lista.append(pack)
    s.close()
