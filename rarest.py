class rarestFirstQueue() :
    
    #instantiate immediately after getting a list of peers from trackers and before handshake
    def __init__(self) :
        self.piecesQueue = []
        self.size = 0
    
    #call the method when piece hash doesn't match, other exception like network failure
    def insertPiece(self, piece) :
        #piece with least number of peers gets priority
        #print(f"Queue size before inserting : {self.size}")
        if self.size == 0 :
            #print("q size 0")
            self.piecesQueue.append(piece)
        else :
            howRare = piece.occurrence
            i = 0
            while i < self.size : 
                if self.piecesQueue[i].occurrence <= howRare :
                    i += 1
                    #print("in if")
                    continue
                else :
                    #print("in else")
                    self.piecesQueue.insert(i, piece)
                    #print("quitting else")
                    break
            if i >= self.size :
                self.piecesQueue.append(piece)
                #print("appended")
        self.size += 1
        #print(f"Queue size after inserting : {self.size}")
    
    #call when downloaded piece fully and hashes matched
    def removePiece(self, piece) :
        try :
            self.piecesQueue.remove(piece)
        except :
            raise Exception("Could not remove piece")
        self.size -= 1