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
            self.piecesQueue.append(piece)
        else :
            howRare = piece.occurrence
            i = 0
            while i < self.size : 
                if self.piecesQueue[i].occurrence <= howRare :
                    i += 1
                    continue
                else :
                    self.piecesQueue.insert(i, piece)
                    break
            if i >= self.size :
                self.piecesQueue.append(piece)
        self.size += 1
    
    #call when downloaded piece fully and hashes matched
    def removePiece(self, piece) :
        try :
            self.piecesQueue.remove(piece)
        except :
            raise Exception("Could not remove piece")
        self.size -= 1