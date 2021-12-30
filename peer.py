import sys
import struct

class Peer() :
    def __init__(self, peer_id, peer_ip, peer_portno) :
        self.state_info = {
            "am_choking" : 1,
            "am_interested" : 0,
            "peer_choking" : 1,
            "peer_interested" : 0
        }
        self.peer_id = peer_id
        self.peer_ip = peer_ip
        self.peer_portno = peer_portno
        self.piece_list = []
