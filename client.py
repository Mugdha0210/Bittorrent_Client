import socket, select, sys, struct, hashlib, bencode, binascii, requests, os, random, string, threading, shutil
from urllib.parse import urlencode, urlunsplit, urlparse
from time import sleep

from pieces import Piece
from message import Message
from peer import Peer

from udp import scrape_udp

class Client() :
    def __init__(self, filename, location, num_peers) :
        #self.my_peer_id = '-MU0707-0a1kf7aDTbLO'
        self.torrent_name = filename
        self.download_dest = location
        self.isMultifile = False
        self.download_files = []    #list of name,length dictionaries
        self.num_peers = num_peers
        self.pieces = b''
        self.num_of_pieces = 0
        self.have_pieces = []
        self.port = 6883
        self.my_peer_id = self.getPeerID()
        self.global_piece_list = {}
        try :
            if not os.path.exists(location):
                os.makedirs(location)
        except Exception as e :
            print(f"Location not accessible as {e}")
            exit(0)

    def getPeerID(self, N = 20) :
        peerId = "-"
        peerId += "MU0707-"
        peerId += ''.join(random.choices(string.ascii_letters + string.digits, k = (N - 8)))
        print(peerId)
        return peerId

    def decodeMultifileInfo(self, files) :
        for file in files :
            file_dict = {
                "name" : file['path'],
                "length" : file['length']
            }
            self.download_files.append(file_dict)
        return

    def getMultifileLength(self) :
        total = 0
        for file in self.info['files'] :
            total += file['length']
        return total

    # def getMultifilePath(self, path) :
    #     full_path = ""
    #     # print(path)
    #     for location in path :
    #         # print(location)
    #         full_path = os.path.join(full_path, location)
    #         print(full_path)
    #         #record file paths and lengths for writeback
    #     return full_path

    def decodeTorrent(self, filename) :
        #do you want port number as user input?
        if filename.split('.')[-1] != "torrent" :
            sys.exit("Please enter .torrent file")
        else :
            torrentFile = open(filename, "rb")
            metainfo = bencode.bdecode(torrentFile.read())
            #print(metainfo)
            try :
                self.tracker_url = ""
                self.tracker_url_list = ""
                if 'announce' in metainfo :
                    # print("announce")
                    self.tracker_url = metainfo['announce']
                if 'announce-list' in metainfo :
                    # print("announce list")
                    self.tracker_url_list = metainfo['announce-list']
                else :
                    self.tracker_url_list = []
                    self.tracker_url_list.append([])
                    self.tracker_url_list[0].append(metainfo['announce'])

                self.info = metainfo['info']
                self.info_hash = hashlib.sha1(bencode.encode(self.info)).digest()
                self.piece_length = self.info['piece length']
                if 'files' in self.info :
                    self.isMultifile = True
                    self.length = self.getMultifileLength()
                else :
                    self.isMultifile = False
                    self.length = self.info['length']
                self.num_of_pieces = self.length // self.piece_length + 1
                self.last_piece_len = self.length % self.piece_length
                self.pieces = self.info['pieces']
                for k in range(self.num_of_pieces) :
                    self.have_pieces.append('0')

            except :
                raise Exception("File not bencoded properly.")

    # def get_num_of_pieces(self) :
    #     self._splitPieces()
    #     return self.num_of_pieces

    def scrape(self, tracker):
        tracker = tracker.lower()
        parsed = urlparse(tracker)
        if parsed.scheme == "udp":
            return scrape_udp(tracker, self.info_hash, self.my_peer_id, self.info, self.num_peers, self.port, self.length)
        if parsed.scheme in ["http", "https"]:
            if "announce" not in tracker:
                raise RuntimeError("%s does not support scrape" % tracker)
            #parsed = urlparse(tracker.replace("announce", "scrape"))
            return self.HTTPTrackerRequest(tracker)
        print(f"Unknown tracker scheme: {parsed.scheme}")

    def HTTPTrackerRequest(self, tracker_url) :
        if not self.isMultifile :
            file_dict = {
                'name' : self.info['name'],
                'length' : self.info['length']
            }
            self.download_files.append(file_dict)
            self.create_file(self.info['name'])
        else :
            files = self.info['files']
            dir_name = self.info['name']
            # files_1 = []
            # for f in files :
            #     files_1.append(dict(f))
            # files = files_1
            # print(files)
            # print(dir_name)
            self.create_dir(dir_name, files)
            self.decodeMultifileInfo(files)
            # #loop through files......every time one get request??
            # length = files[1]['length']
            # print(length)
            # #self.length = length
            # path = files[1]['path']
        query_params = urlencode({"info_hash" : self.info_hash, "peer_id" : self.my_peer_id, "port" : self.port, \
                                "uploaded" : 0, "downloaded" : 0, "left" : self.length, \
                                "event" : "started",\
                                "numwant" : self.num_peers
                                })
        lookup_url = f"{tracker_url}?{query_params}"
        r = requests.get(lookup_url)
        content = r.content
        x = dict(bencode.bdecode(content))
        # print(x)
        if content == b'<title>Invalid Request</title>\n' :
            return {"Error " : "Invalid Request"}
        return x

    def create_dir(self, name, files) :
        try :
            dir_path = os.path.join(self.download_dest, name)
            if os.path.exists(dir_path) :
                shutil.rmtree(dir_path)
            os.makedirs(dir_path)
            for file in files :
                # print("in create_dir", file['path'])
                file_path = os.path.join(dir_path)
                for location in file['path'] :
                    # file_name = str(file['path'])
                    # print(dir_path, str(file_name))
                    file_path = os.path.join(file_path, location)
                print(file_path)
                if not os.path.exists(file_path) :
                    os.makedirs(os.path.join(self.download_dest, file_path))
        except Exception as e:
            print(f"Could not create directory for writeback as {e}")
            # raise
            exit(0)
        return

    def create_file(self, file_path) :
        try :
            print(file_path)
            self.fd = os.open(os.path.expanduser(os.path.join(self.download_dest, file_path)), os.O_RDWR|os.O_CREAT)
        except Exception as e:
            print(f"Could not open file as {e}")
            exit(0)
        return

    def getPeers(self, tracker) :
        response = self.scrape(tracker)
        #response as a dictionary
        if 'Error' in response or 'failure reason' in response :
            return []
        returnList = []
        if type(response) == list :
            return response
        elif type(response['peers']) == list :
            returnList = response['peers']
            list1 = [dict(l) for l in returnList]
            if len(list1) > self.num_peers :
                list1 = list1[ : self.num]
        else :
            try :
                binary_ip = response['peers']
                offset = 0
                n = len(binary_ip)
                list1 = []
                while offset != n :
                    ip1 = struct.unpack_from("!i", binary_ip, offset)[0] # ! = network order(big endian); i = int
                    ip = socket.inet_ntoa(struct.pack("!i", ip1))
                    offset += 4 # save where the first ip ends and the port begins
                    port = struct.unpack_from("!H", binary_ip, offset)[0] # H = unsigned short
                    list1.append({"ip" : ip, "port" : port})
                    offset += 2
                if len(list1) > self.num_peers :
                    list1 = list1[ : self.num]
            except Exception as e:
                raise Exception(f"Exception in getting peers as {e}")
        # print(list1)
        return list1


    def generateHandshake(self, my_peer_id) :
        assert len(self.info_hash) == 20
        assert len(my_peer_id) == 20

        handshake_msg = (chr(19) + "BitTorrent protocol" + chr(0) * 8).encode('utf-8')
        handshake_msg = b"".join([handshake_msg, self.info_hash, my_peer_id.encode('utf-8')])
        #print("sending", handshake_msg)
        return handshake_msg

    def checkReplyHandshake(self, reply_handshake, this_peer, peer_tag) :
        #exp_protocol = b'\x13BitTorrent protocol'
        exp_infohash = self.info_hash
        #CHECK FOR PEER ID TYPE!
        try :
            exp_peerid = this_peer.peer_id.encode('utf-8')
        except :
            #peer id already a bytes object
            exp_peerid = this_peer.peer_id

        if this_peer.peer_id == "" :
            if reply_handshake[28:-20] == exp_infohash  :
                this_peer.peer_id = reply_handshake[-20:]
                print(peer_tag, "Reply handshake validated.")
                return True

        elif (reply_handshake[-20:] == exp_peerid) and (reply_handshake[28:-20] == exp_infohash) :
            print(peer_tag, "Reply handshake validated.")
            return True
        else :
            return False

    def _splitPieces(self) :
        pieces = self.pieces
        #print(len(pieces))
        my_piece_list = []
        i = 0
        j = 0
        n = len(pieces)
        while i < n :
            if i >= (n - 20) :
                my_piece_list.append((pieces[i : n], j, (n - i)))
            else :
                my_piece_list.append((pieces[i : i + 20], j, 20))
            i += 20
            j += 1
        #print(my_piece_list)
        self.num_of_pieces = j
        return my_piece_list

    def write_to_location(self, piece):
        if self.isMultifile :
            # print("w_1")
            self.fd = os.open(os.path.expanduser(os.path.join(self.download_dest, 'temp')), os.O_RDWR|os.O_CREAT)
            # print("w_2")
        #else :
        #    self.fd = os.open(os.path.expanduser(os.path.join(self.download_dest, self.info['name'])), os.O_RDWR|os.O_CREAT)
        # print("w_3")
        offset_from_start = piece.index * self.piece_length
        # print("w_4")
        os.lseek(self.fd, offset_from_start, os.SEEK_SET)
        # print("w_5")
        try :
            os.write(self.fd, piece.data)
        except Exception as e:
            print(f"Could not write to location as {e}")
            raise Exception

    def writeMultifile(self) :
        # print(1)
        with open(os.path.join(self.download_dest, 'temp')) as f_buffer :
            # print(2)
            for file in self.download_files :
                # print(3)
                with open(os.path.join(self.download_dest, file['name']), "w") as f_dest :
                    # print(5)
                    for byte in range(file['length']) :
                        print("before f_dest write")
                        f_dest.write(f_buffer.read(1))
                        print("written")
                    f_dest.close()
                    print("after close")
        print("before fclose")
        f_buffer.close()
        return

    def connect_peer(self, this_peer, outboundSocket) :
        #for printing only
        peer_tag = this_peer.peer_ip + " : " + str(this_peer.peer_portno) + " ---"
        # try :
        #     outboundSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #     outboundSocket.connect((str(this_peer.peer_ip), int(this_peer.peer_portno)))
        #     print(peer_tag, "Connected")
        # #outboundSocket.setblocking(False)
        # except :
        #     print(peer_tag, "Did not connect")

            #######################################################
        try :
            handshake_msg = self.generateHandshake(self.my_peer_id)
            outboundSocket.send(handshake_msg)
        except Exception as e:
            print(peer_tag, f"Handshake not sent because {e}")
        try :
            sleep(2)
            recv_buffer = outboundSocket.recv(2048)
            reply_handshake = recv_buffer[:68]
            if not len(reply_handshake) :
                print(peer_tag, "No reply, dropping peer")
                outboundSocket.close()
                return
            else :
                #print("received", reply_handshake)
                if not self.checkReplyHandshake(reply_handshake, this_peer, peer_tag) :
                    print(peer_tag, "Reply handshake invalid, dropping peer")
                    outboundSocket.close()
                    return
                else :
                    first_msg = Message()
                    first_msg_prefix = recv_buffer[68:72]
                    first_msg.findLength(first_msg_prefix)
                    first_msg.id = recv_buffer[72]
                    first_msg.payload = recv_buffer[73:(73 + first_msg.len - 1)]
                    # print(len(first_msg.payload))
                    first_msg.identify()
                    if first_msg.type == "null":
                        pass
                    else :
                        print(peer_tag, first_msg.type, "received")
                    if first_msg.type == "bitfield" :
                        #checking validity of bitfield
                        bitwise_payload = []
                        for byte in first_msg.payload :
                            bstr = f'{byte:0>8b}'
                            for bit in bstr :
                                bitwise_payload.append(bit)

                        #initialize have_pieces list
                        spares = (first_msg.len - 1) * 8 - self.num_of_pieces
                        this_peer.piece_list = bitwise_payload[: self.num_of_pieces]
                        #m = len(this_peer.piece_list)
                        self.global_piece_list[this_peer] = this_peer.piece_list
                    elif first_msg.type == "have" :
                        piece_index = first_msg.handleHave()
                        this_peer.piece_list[piece_index] = '1'
                        self.global_piece_list[this_peer] = this_peer.piece_list
                    else :
                        print(peer_tag, "Unrecognized message right after handshake, dropping peer")
                        outboundSocket.close()
                        return
        except Exception as e:
            print(peer_tag, f"-----{e}-----\n")

    def getPieces(self, peer_list, sock_list, p1) :
        for this_peer in peer_list :
            outboundSocket = sock_list[this_peer]
            peer_tag = this_peer.peer_ip + " : " + str(this_peer.peer_portno) + " ---"
            try :
                piece_length = self.piece_length
                block_length = 2 ** 14
                r = bytes()
                m = len(this_peer.piece_list)
                while True :
                    if this_peer.state_info['am_interested'] and not this_peer.state_info['peer_choking'] :
                        print("in if")
                        j = p1.index
                        if self.have_pieces[j] == '1' :
                            return


                        if this_peer.piece_list[j] == '0' :
                            print(peer_tag, f"I do not have piece {j}")
                            continue


                        r = bytes()
                        #outboundSocket.settimeout(10)
                        n = piece_length // block_length
                        if j == m - 1 :
                            piece_length = self.last_piece_len
                            if piece_length % block_length != 0 :
                                n = piece_length // block_length + 1
                        i = 0
                        while i < n :
                            #sending request.
                            message_id = 6
                            payload_length = 13
                            block_index = i
                            piece_index = j
                            block_offset = int(block_index * block_length)
                            if i == (n - 1)  :
                                block_length = piece_length - block_offset
                            if this_peer.state_info['peer_choking'] == 0 :
                                outboundSocket.send(struct.pack(">IBIII",payload_length, message_id, piece_index, block_offset, block_length))
                            else :
                                break
                            print(peer_tag, f"Request sent for block {block_offset}")
                            sleep(2)
                            #receive upto id of unknown messages.
                            recv_buffer = outboundSocket.recv(5)
                            some_msg = Message()


                            prefix = recv_buffer[:4]


                            print(prefix)
                            if len(prefix) >= 4 :
                                some_msg.findLength(prefix)
                            else :
                                break
                            if some_msg.len == 0 :
                                some_msg.id = b''
                            else :
                                some_msg.id = recv_buffer[4]


                            some_msg.identify()
                            if some_msg.type == "null":
                                pass
                            else :
                                print(peer_tag, some_msg.type, "received")
                            if some_msg.type == "null" :
                                pass
                            if some_msg.type == "unchoke" :
                                this_peer.state_info['peer_choking'] = 0

                            elif some_msg.type == "choke" :
                                this_peer.state_info['peer_choking'] = 1
                                #cannot request until unchoked.
                                continue
                            elif some_msg.type == "interested" :
                                this_peer.state_info['peer_interested'] = 1
                                #DECIDE IF I WANT TO UNCHOKE THEM AND DO IT

                            elif some_msg.type == "not interested" :
                                this_peer.state_info['peer_interested'] = 0
                            elif some_msg.type == "have" :
                                piece_index = some_msg.handleHave()
                                this_peer.piece_list[piece_index] = '1'
                            elif some_msg.type == "request" :
                                outboundSocket.recv(12)
                                if this_peer.state_info['interested'] and not this_peer.state_info['am_choking'] :
                                    #THIS IS SUPPOSED TO HAPPEN ON THE INBOUND SOCKET
                                    pass
                                else :
                                    #ignore
                                    pass
                            elif some_msg.type == "cancel" :
                                i -= 1
                                outboundSocket.recv(12)
                                pass
                            elif some_msg.type == "port" :
                                i -= 1
                                outboundSocket.recv(2)
                                pass
                            elif some_msg.type == "keep-alive" :
                                i -= 1
                                pass
                            elif some_msg.type == "piece" :
                                #receiving blocks
                                x = outboundSocket.recv(8 + block_length)
                                if len(x) == 0 :
                                    break
                                begin = struct.unpack(">I", x[4:8])[0]
                                if begin == block_offset :
                                    print(peer_tag, f"Received block offset {block_offset}")
                                    r += x[8:]
                                else :
                                    print(peer_tag, "Received wrong block")
                                    break

                            else :
                                print(peer_tag, "Unrecognized message")
                                break
                            i += 1
                        l1 = self._splitPieces()

                        if p1.matchHash(r) :
                            print(peer_tag, f"Downloaded piece {j}")
                            p1.data = r
                            self.write_to_location(p1)
                            self.have_pieces[j] = '1'
                            if j == (m - 1) :
                                if self.isMultifile :
                                    self.writeMultifile()
                        else :
                            print(peer_tag, "Error while matching Hash Value")
                    #IF THIS PEER HAS A PIECE I DON'T HAVE PLUS RAREST FIRST
                    if this_peer.state_info['am_interested'] == 0 :
                        #send interested
                        interested_msg_id = 2
                        payload_length = 1
                        outboundSocket.send(struct.pack(">IB", payload_length, interested_msg_id))
                        this_peer.state_info['am_interested'] = 1
                    # IF THIS PEER DOES NOT HAVE SOMETHING I DON'T HAVE PLUS RAREST FIRST
                    # if this_peer.state_info['am_interested'] == 1 :
                    #     #send not interested
                    #     notinterested_msg_id = 3
                    #     payload_length = 1
                    #     outboundSocket.send(struct.pack(">IB", payload_length, notinterested_msg_id))
                    #     this_peer.state_info['am_interested'] = 0
                    #receive upto id of unknown messages.
                    recv_buffer = outboundSocket.recv(5)
                    some_msg = Message()
                    prefix = recv_buffer[:4]
                    some_msg.findLength(prefix)
                    if some_msg.len == 0 :
                        some_msg.id = b''
                    else :
                        some_msg.id = recv_buffer[4]
                    some_msg.identify()
                    print(peer_tag, some_msg.type, "received")
                    if some_msg.type == "unchoke" :
                        this_peer.state_info['peer_choking'] = 0
                    elif some_msg.type == "choke" :
                        this_peer.state_info['peer_choking'] = 1
                        #cannot request until unchoked.
                        continue
                    elif some_msg.type == "interested" :
                        this_peer.state_info['peer_interested'] = 1
                        #DECIDE IF I WANT TO UNCHOKE THEM AND DO IT

                    elif some_msg.type == "not interested" :
                        this_peer.state_info['peer_interested'] = 0
                    elif some_msg.type == "have" :
                        piece_index = some_msg.handleHave()
                        this_peer.piece_list[piece_index] = '1'
                    elif some_msg.type == "request" :
                        outboundSocket.recv(12)
                        if this_peer.state_info['interested'] and not this_peer.state_info['am_choking'] :
                            #THIS IS SUPPOSED TO HAPPEN ON THE INBOUND SOCKET
                            # some_msg.payload = outboundSocket.recv(8)
                            # some_msg.handleRequest()
                            pass
                        else :
                            #ignore
                            pass
                    elif some_msg.type == "cancel" :
                        outboundSocket.recv(12)
                        pass
                    elif some_msg.type == "port" :
                        outboundSocket.recv(2)
                        pass
                    elif some_msg.type == "keep-alive" :
                        pass
                    elif some_msg.type == "piece" :
                        print(peer_tag, "Not supposed to come to this piece")

                    else :
                        print(peer_tag, "Unrecognized message")

                print("\n")
            except Exception as e:
                print(peer_tag, f"-----{e}-----\n")
                # raise
