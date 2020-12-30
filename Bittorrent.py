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

    # u = (speed_test.getNetSpeed()['Up_speed'] / 2**20)
    # d = (speed_test.getNetSpeed()['Down_speed'] / 2**20)
    # print(f"Set upload speed as default - {u} ? Enter y or n.")
    # flag = input()
    # try :
    #     if flag == 'n' :
    #         print("Enter upload speed in Mbits : ")
    #         up_user = float(input())
    #     elif flag == 'y' :
    #         print("Default upload speed set.")
    #         up_user = u
    #     else :
    #         print("Invalid user input")
    #         exit(0)
    # except Exception as e:
    #     print(f"User input invalid as {e}")
    # print(f"Set download speed as default - {d} ? Enter y or n.")
    # flag = input()
    # try :
    #     if flag == 'n' :
    #         print("Enter download speed in Mbits : ")
    #         down_user = float(input())
    #     elif flag == 'y' :
    #         print("Default download speed set.")
    #         down_user = u
    #     else :
    #         exit(0)
    # except Exception as e:
    #     print(f"User input invalid as {e}")
    this_client = Client(sys.argv[1], sys.argv[2], num_peers)
    this_client.decodeTorrent(sys.argv[1])
    t = this_client.tracker_url_list
    #print(t)
    for t1 in t :
        peerinfo_list = this_client.getPeers(t1[0])
        # print(peerinfo_list)
        if len(peerinfo_list) != 0 :
            break
    sock_list = {}
    n_l = len(peerinfo_list)
    try :
        i = 0
        count = 30
        while i  < n_l :
            #print("in for")
            if i == count :
                break
            peerinfo = peerinfo_list[i]
            try :
                #threading._start_new_thread(connect_peer, (peerinfo, abc))
                #threading.Thread(target = connect_peer, args = (peerinfo,)).start()
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
                    #print("a")
                    outboundSocket.connect((str(this_peer.peer_ip), int(this_peer.peer_portno)))

                    #print("b")
                    sock_list[this_peer] = outboundSocket

                    #print("c")
                    print(peer_tag, "Connected")
                    thread_obj = threading.Thread(None, this_client.connect_peer, args = (this_peer, outboundSocket))
                    thread_obj.start()
                except Exception as e:
                    count += 1
                    print(peer_tag, f"Did not connect because {e}")
                    # raise

                #print("connect called, new thread started")
                thread_obj.join()
                #print(this_peer.peer_ip + " : " + str(this_peer.peer_portno) + " ---" + " Joined")
            except Exception as e :
                pass
                # print(f"new thread not started due to {e}.")
                # raise
            i += 1

        #time.sleep(5 * n_l)
        #print(this_client.global_piece_list)
        l1 = this_client._splitPieces()
        #print(l1)
        q = rarestFirstQueue()

        for i in range(this_client.num_of_pieces) :
            if i == this_client.num_of_pieces - 1 :
                #print("-1 if")
                p1 = Piece(l1[i][0], i, this_client.last_piece_len, bytes())
                #print("in if")
            else :
                #print("-1 else")
                p1 = Piece(l1[i][0], i, this_client.piece_length, bytes())
                #print("in else")
            for peer in this_client.global_piece_list :
                m = len(this_client.global_piece_list[peer])
                #print(m)
                if i >= m :
                    continue
                #print(0)
                if this_client.global_piece_list[peer][i] == '1' :
                    p1.occurrence += 1
                    #print(1)
                #print(2)
            q.insertPiece(p1)
            #print(f"piece {i} inserted")
        print(len(q.piecesQueue))
        time.sleep(2)
        for p in q.piecesQueue :
            #peer_tag = p.peer_ip + " : " + str(p.peer_portno) + " ---"
            #print(p.index)
            peer_list = []
            for peer in this_client.global_piece_list :
                #print("abc")
                if this_client.global_piece_list[peer][p.index] == '1':
                    peer_list.append(peer)
                    #print("pqr")
            thread_obj = threading.Thread(None, this_client.getPieces, args = (peer_list, sock_list, p))
            thread_obj.start()

            thread_obj.join()

        #for p in q.piecesQueue :
            #print(p.occurrence)
    except Exception as e:
        print(f"Error from client : {e}")
        raise
    #print("hello")
