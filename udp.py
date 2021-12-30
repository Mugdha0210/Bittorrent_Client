import socket
from socket import *
import select
import sys
import struct
import hashlib
import bencode
import binascii
import requests
import os
import random
import string
import threading
from urllib.parse import urlencode, urlunsplit, urlparse
from time import sleep


def scrape_udp(tracker, info_hash, my_peer_id, info, num_peers, my_port, total_length):
    try :
        i = int("41727101980", 16)
        j = 0
        prot_id = i.to_bytes(8, "big")
        action = j.to_bytes(4, "big")
        random_num = random.randint(1, 65535)
        t_id = random_num.to_bytes(4, "big")
        msg = prot_id + action + t_id
        udp_sck = socket(AF_INET, SOCK_DGRAM)
        udp_sck.settimeout(5)
        ur = tracker[6:]
        urp = ur.split(":")
        port = urp[-1].split("/")
        print("to send : ", (urp[0], int(port[0])))
        udp_sck.sendto(msg, (urp[0], int(port[0])))
        reply, addr = udp_sck.recvfrom(1024)
        trans_id = reply[4:8]
        conn_id = reply[8:16]
        ##checks for action
        if trans_id == t_id :
            j = 1
            action = j.to_bytes(4, "big")
            peer_id = bytes(my_peer_id, "utf-8")
            j = 0
            d = j.to_bytes(8, "big")
            j = int(total_length)
            l = j.to_bytes(8, "big")
            j = 0
            u = j.to_bytes(8, "big")
            event = j.to_bytes(4, "big")
            ipadr = j.to_bytes(4, "big")
            random_num = random.randint(1, 65535)
            key = random_num.to_bytes(4, "big")
            j = int(num_peers)
            num_want = j.to_bytes(4, "big")
            j = int(my_port)
            po = j.to_bytes(8, "big")
            msg = conn_id + action + trans_id + info_hash + peer_id + d + l + u + event + ipadr + key + num_want + po
            udp_sck.sendto(msg, (urp[0], int(port[0])))
            reply, addr = udp_sck.recvfrom(1024)
            nantar = reply[:20]
            atta = reply[20:]
            binary_ip = atta
            offset = 0
            n = len(binary_ip)
            list1 = []
            while offset != n :
                ip1 = struct.unpack_from("!i", binary_ip, offset)[0] # ! = network order(big endian); i = int
                ip = inet_ntoa(struct.pack("!i", ip1))
                offset += 4 # save where the first ip ends and the port begins
                port = struct.unpack_from("!H", binary_ip, offset)[0] # H = unsigned short
                list1.append({"ip" : ip, "port" : port})
                offset += 2
            if len(list1)  > num_peers :
                list1 = list1[:num_peers]
            return list1

    except Exception as e:
        print(f"Cannot get peers from udp tracker as {e}")
        return []
