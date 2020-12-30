import hashlib
class Piece(object) :
    def __init__(self, piece_hash, piece_index : int, piece_size : int, data : bytes):
        self.index = piece_index
        self.blocks = []
        self.hash = piece_hash
        self.occurrence = 0
        self.size = piece_size
        self.data = data

    def getOccurrence(self, occur_list : []) :
        self.occurrence = sum(occur_list)
        return self.occurrence

    def matchHash(self, data) :
        # print("in pieces")
        recvd_piece_hash = hashlib.sha1(data).digest()
        # print(recvd_piece_hash)
        return self.hash == recvd_piece_hash
