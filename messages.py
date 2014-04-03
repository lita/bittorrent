from bitstring import BitArray

class Message(object):
	def __init__(self, payload):
		self.payload = payload

class KeepAlive(Message):
	pass

class Choke(Message):
	pass

class Unchoke(Message):
	pass

class Interested(Message):
	pass

class NotInterested(Message):
	pass

class Have(Message):
    protocol_args = ['index']

class Bitfield(Message):
    protocol_extended = 'bitfield'
    def __init__(self, payload, pieces):

class Request(Message):
    protocol_args = ['index','begin','length']
    
class Piece(Message):
    protocol_args = ['index','begin']
    protocol_extended = 'block'

class Cancel(Message):   
    protocol_args = ['index','begin','length']

class Port(Message):
    protocol_extended = 'listen_port'
