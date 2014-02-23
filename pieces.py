BLOCK_SIZE = 2**14

class Piece(object):
	def __init__(self, pieceIndex, pieceSize):
		self.pieceIndex = pieceIndex
		self.pieceSize = pieceSize
		self.blocks = []

	def addBlock(self, offset, data):
		pass

class Blocks(object):
	def __init__(self, offset, payload):
		self.offset = offset
		self.payload = payload

