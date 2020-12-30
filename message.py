import sys
import struct

class Message() :
    def __init__(self) :
        self.type = "null"
        self.len = -1
        self.id = b''
        self.payload = bytes()

    def findLength(self, prefix) :
        self.len = struct.unpack('>I', prefix)[0]

    def identify(self) :
        if self.len == 0 and not self.id :
            self.type = "keep-alive"
        elif self.len == 1 :
            if self.id == 0 :
                self.type = "choke"
            if self.id == 1 :
                self.type = "unchoke"
            if self.id == 2 :
                self.type = "interested"
            if self.id == 3 :
                self.type = "not interested"
        elif self.id == 4 and self.len == 5 :
            self.type = "have"
        elif self.id == 5 :
            self.type = "bitfield"
        elif self.id == 6 and self.len == 13 :
            self.type = "request"
        elif self.id == 7 :
            self.type = "piece"
        elif self.id == 8 :
            self.type = "cancel"
        elif self.id == 9 :
            self.type = "port"
        else :
            pass

    def handleHave(self) :
        # print("Dealing with have.")
        piece_index = self.payload
        return piece_index


    def handleBitfield(self) :
        piece_list = []
        # print("Dealing with bitfield.")
        for index in self.payload :
            bstr = f'{index:0>8b}'
            #print(bstr)
            for i in bstr :
                #print(i)
                piece_list.append(i)
        return piece_list
