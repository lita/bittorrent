import math
import hashlib
import pdb

from bitstring import BitArray

BLOCK_SIZE = 2**14

class Piece(object):
    """
    Holds all the information about the piece of a file. Holds the hash of that piece 
    as well, which is given by the tracker. 

    The actual data (which are just bytes) is stored in Block class till the very end, 
    where all the data is concatenated together and stored in self.block. This is 
    so that we save memory. 
    TODO: Change it so that all the data is not stored in RAM
    """
    def __init__(self, pieceIndex, pieceSize, pieceHash):
        self.pieceIndex = pieceIndex
        self.pieceSize = pieceSize
        self.pieceHash = pieceHash
        self.finished = False
        self.num_blocks = int(math.ceil(float(pieceSize)/BLOCK_SIZE))
        self.bitField = BitArray(self.num_blocks)
        self.blocks = []
        self.generateBlocks()

    def generateBlocks(self):
        offset = 0
        for i in range(self.num_blocks):
            if i == self.num_blocks-1: 
                # Last piece. Need to handle it specially.
                block = Blocks(self.pieceSize-offset, offset)
            else:
                block = Blocks(BLOCK_SIZE, offset)

            self.blocks.append(block)
            offset += BLOCK_SIZE

    def addBlock(self, offset, data):
        if offset == 0:
            index = 0
        else:
            index = offset/BLOCK_SIZE

        self.blocks[index].addPayload(data)
        self.bitField[index] = True
        finished = all(self.bitField)
        if finished:
            if self.checkHash():
                self.finished = True
            else:
                # Hash doesn't match. Need to redownload and set the the bitField.
                self.bitField = BitArray(self.num_blocks)

    def checkHash(self):
        allData = ''
        for block in self.blocks:
            allData += block.data

        hashedData = hashlib.sha1(allData).digest()
        if hashedData == self.pieceHash:
            self.block = allData
            return True
        else:
            return False

class Blocks(object):
    def __init__(self, size, offset):
        self.size = size
        self.offset = offset
        self.data = None

    def addPayload(self, payload):
        self.data = payload