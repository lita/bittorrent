import math
import hashlib

from bitstring import BitArray

BLOCK_SIZE = 2**14

class Piece(object):
    """
    Holds all the information about the piece of a file. Holds the hash of that 
    piece as well, which is given by the tracker. 

    The Piece class also tracks what blocks are avialable to download.

    The actual data (which are just bytes) is stored in Block class till the 
    very end, where all the data is concatenated together and stored in 
    self.block. This is so that we save memory.

    TODO: Change it so that all the data is not stored in RAM

    self.pieceIndex     -- The index of where this piece lives in the entire 
                           file.
    self.pieceSize      -- Size of this piece. All pieces should have the same 
                           size besides the very last one.
    self.pieceHash      -- Hash of the piece to verify the piece we downloaded.
    self.finished       -- Flag to tell us when the piece is finished 
                           downloaded.
    self.num_blocks     -- The amount of blocks this piece contains. Again, it
                           should all be the same besides the last one.
    self.blockTracker   -- Keeps track of what blocks are still needed to 
                           download. This keeps track of which blocks to request
                           to peers.
    self.blocks         -- The actual block objects that store the data.
    """

    def __init__(self, pieceIndex, pieceSize, pieceHash):
        self.pieceIndex = pieceIndex
        self.pieceSize = pieceSize
        self.pieceHash = pieceHash
        self.finished = False
        self.num_blocks = int(math.ceil(float(pieceSize)/BLOCK_SIZE))
        self.blockTracker = BitArray(self.num_blocks)
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
        self.blockTracker[index] = 1
        self.finished = all(self.blockTracker)

        if self.finished:
            return self.checkHash()

        return True

    def reset(self):
        """Reset the piece. Used when the data is bad and need to redownload"""
        self.blockTracker = BitArray(self.num_blocks)
        self.finished = False

    def checkHash(self):
        allData = ''
        for block in self.blocks:
            allData += block.data

        hashedData = hashlib.sha1(allData).digest()
        if hashedData == self.pieceHash:
            self.block = allData
            return True
        else:
            piece.reset()
            return False

class Blocks(object):
    """Block object that stores the data and offset."""
    def __init__(self, size, offset):
        self.size = size
        self.offset = offset
        self.data = None

    def addPayload(self, payload):
        self.data = payload