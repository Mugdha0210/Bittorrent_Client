import sys
import threading
import socket
import time
from pieces import Piece
from message import Message
from peer import Peer
from rarest import rarestFirstQueue
from client import Client
# import speed_test

if __name__ == "__main__" :
    if len(sys.argv) < 3 or len(sys.argv) > 4 :
        print("Usage : python3 bittorrent_client.py <filename.torrent> <location> <number_of_peers (default = 50)>")
        exit(0)
    if len(sys.argv) == 3 :
        num_peers = 50
    else :
        if int(sys.argv[3]) > 0 :
            num_peers = int(sys.argv[3])
        else :
            print("Number of peers should be more than 0.")
            exit(0)

    this_client = Client(sys.argv[1], sys.argv[2], num_peers)
    this_client.decodeTorrent(sys.argv[1])
    t = this_client.tracker_url_list
    for t1 in t :
        peerinfo_list = this_client.getPeers(t1[0])
        if len(peerinfo_list) != 0 :
            break
    sock_list = {}
    n_l = len(peerinfo_list)
    try :
        i = 0
        count = 30
        while i  < n_l :
            if i == count :
                break
            peerinfo = peerinfo_list[i]
            try :
                peer_ip = peerinfo['ip']
                if 'peer id' in peerinfo :
                    peer_id = peerinfo['peer id']
                else :
                    peer_id = ""
                peer_portno = peerinfo['port']
                this_peer = Peer(peer_id, peer_ip, peer_portno)
                peer_tag = this_peer.peer_ip + " : " + str(this_peer.peer_portno) + " ---"
                try :
                    outboundSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    outboundSocket.settimeout(5)
                    outboundSocket.connect((str(this_peer.peer_ip), int(this_peer.peer_portno)))

                    sock_list[this_peer] = outboundSocket

                    print(peer_tag, "Connected")
                    thread_obj = threading.Thread(None, this_client.connect_peer, args = (this_peer, outboundSocket))
                    thread_obj.start()
                except Exception as e:
                    count += 1
                    print(peer_tag, f"Did not connect because {e}")
                    # raise

                thread_obj.join()
            except Exception as e :
                pass
            i += 1

        #time.sleep(5 * n_l)
        l1 = this_client._splitPieces()
        q = rarestFirstQueue()

        for i in range(this_client.num_of_pieces) :
            if i == this_client.num_of_pieces - 1 :
                p1 = Piece(l1[i][0], i, this_client.last_piece_len, bytes())
            else :
                p1 = Piece(l1[i][0], i, this_client.piece_length, bytes())
            for peer in this_client.global_piece_list :
                m = len(this_client.global_piece_list[peer])
                if i >= m :
                    continue
                if this_client.global_piece_list[peer][i] == '1' :
                    p1.occurrence += 1
            q.insertPiece(p1)
        print(len(q.piecesQueue))
        time.sleep(2)
        for p in q.piecesQueue :
            peer_list = []
            for peer in this_client.global_piece_list :
                if this_client.global_piece_list[peer][p.index] == '1':
                    peer_list.append(peer)
            thread_obj = threading.Thread(None, this_client.getPieces, args = (peer_list, sock_list, p))
            thread_obj.start()

            thread_obj.join()

    except Exception as e:
        print(f"Error from client : {e}")
        raise
