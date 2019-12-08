# Written by Aaron Cohen -- 1/14/2013
# Brought to you by BitTorrent, Inc.
# "We're not just two guys in a basement in Sweden." TM
#
# This work is licensed under a Creative Commons Attribution 3.0 Unported License.
# See: http://creativecommons.org/licenses/by/3.0/

import sys
import re
import socket
import time
import struct


def ip_is_local(ip_string):
    """
    Uses a regex to determine if the input ip is on a local network. Returns a boolean. 
    It's safe here, but never use a regex for IP verification if from a potentially dangerous source.
    """
    combined_regex = "(^10\.)|(^172\.1[6-9]\.)|(^172\.2[0-9]\.)|(^172\.3[0-1]\.)|(^192\.168\.)"
    return re.match(combined_regex,
                    ip_string) is not None  # is not None is just a sneaky way of converting to a boolean

def get_local_ip():

    try:
        from netifaces import interfaces, ifaddresses, AF_INET
        ip = '127.0.0.1'
        li = []

        for ifacename in interfaces():
            for add in ifaddresses(ifacename).setdefault(AF_INET, [{'addr':'00'}]):
                if add['addr'] != '00' and add['addr']!='lo0':
                    li.append(add['addr'])

        if ip in li:
            li.remove(ip)
        if '172.17.42.1' in li:
            li.remove('172.17.42.1')
        if not len(li):
            return [ip]
        return li

    except:
        print ("no tienes instalado netifaces")

    return ["127.0.0.1"]


def create_socket(multicast_ip, port):
    """
    Creates a socket, sets the necessary options on it, then binds it. The socket is then returned for use.
    """

    local_ip = get_local_ip()[0]

    # create a UDP socket
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # allow reuse of addresses
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # set multicast interface to local_ip
    my_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(local_ip))

    # Set multicast time-to-live to 2...should keep our multicast packets from escaping the local network
    my_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    # Construct a membership request...tells router what multicast group we want to subscribe to
    membership_request = socket.inet_aton(multicast_ip) + socket.inet_aton(local_ip)

    # Send add membership request to socket
    # See http://www.tldp.org/HOWTO/Multicast-HOWTO-6.html for explanation of sockopts
    my_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership_request)

    # Bind the socket to an interface.
    # If you bind to a specific interface on the Mac, no multicast data will arrive.
    # If you try to bind to all interfaces on Windows, no multicast data will arrive.
    # Hence the following.
    # ~ if sys.platform.startswith("darwin"):
    # ~ my_socket.bind(('0.0.0.0', port))
    # ~ else:
    # ~ my_socket.bind((local_ip, port))
    my_socket.bind(('0.0.0.0', port))
    return my_socket


multicast_ip = "239.255.4.3"
multicast_port = 1234


def listen_loop():
    port = multicast_port
    my_socket = create_socket(multicast_ip, port)
    while True:
        # Data waits on socket buffer until we retrieve it.
        # NOTE: Normally, you would want to compare the incoming data's source address to your own, and filter it out
        #       if it came rom the current machine. Everything you send gets echoed back at you if your socket is
        #       subscribed to the multicast group.
        data, address = my_socket.recvfrom(4096)
        data = data.decode()
        yield data


def announce_loop(message):
    port = multicast_port
    # Offset the port by one so that we can send and receive on the same machine
    my_socket = create_socket(multicast_ip, port + 1)
    # NOTE: Announcing every second, as this loop does, is WAY aggressive. 30 - 60 seconds is usually
    #       plenty frequent for most purposes.
    while True:
        msg = message.encode()
        # Send data. Destination must be a tuple containing the ip and port.
        my_socket.sendto(msg, (multicast_ip, port))
        time.sleep(3.5)


if __name__ == '__main__':
    # Choose an arbitrary multicast IP and port.
    # 239.255.0.0 - 239.255.255.255 are for local network multicast use.
    # Remember, you subscribe to a multicast IP, not a port. All data from all ports
    # sent to that multicast IP will be echoed to any subscribed machine.
    # multicast_address = "239.255.4.3"
    # multicast_port = 1234

    # When launching this example, you can choose to put it in listen or announce mode.
    # Announcing doesn't require binding to a port, but we do it here just to reuse code.
    # It binds to the requested port + 1, allowing you to run the announce and listen modes
    # on the same machine at the same time.

    # In a real case, you'll most likely send and receive from the same port using Gevent or Twisted,
    # so the code in create_socket() will apply more directly.

    if sys.argv[1] == "listen":
        for i in listen_loop():
            print(i)
    elif sys.argv[1] == "announce":
        announce_loop("i am here, (ip,port)")
    else:
        exit("Run 'multicast_example.py listen' or 'multicast_example.py announce'.")

