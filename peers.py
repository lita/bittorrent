import hashlib
import socket
import math

import bencode
import requests
from bitstring import BitArray

from pieces import Piece

class PeerManager(object):
    """
    Holds the tracker information and the list of ip addresses and ports.
    """

    def __init__(self, trackerFile):
        """
        Initalizes the PeerManager, which handles all the peers it is connected
        to.

        Input:
        trackerFile -- takes in a .torrent tracker file.

        Instance Variables:
        self.peer_id     -- My id that I give to other peers.
        self.peers       -- List of peers I am currently connected to. Contains 
                            Peer Objects
        self.pieces      -- List of Piece objects that store the actual data we
                            we are downloading.
        self.tracker     -- The decoded tracker dictionary.
        self.infoHash    -- SHA1 hash of the file we are downloading.
        """
        self.peer_id = '-lita38470993824756-'
        self.peers = []
        self.pieces = []
        self.tracker = bencode.bdecode(open(trackerFile,'rb').read())
        bencodeInfo = bencode.bencode(self.tracker['info'])
        self.infoHash = hashlib.sha1(bencodeInfo).digest()
        self.getPeers()
        self.generatePieces()
        self.peer_id = '-lita38470993887523-'

    def isTorrentFinishedDownloading(self):
        return all([x.finished for x in self.pieces])

    def generatePieces(self):
        print "Initalizing..."
        pieceHashes = self.tracker['info']['pieces']
        pieceLength = self.tracker['info']['piece length']
        if 'files' in self.tracker['info']:
            files = self.tracker['info']['files']
            totalLength = sum([file['length'] for file in files])
            self.numPieces =  int(math.ceil(float(totalLength)/pieceLength))
        else:
            totalLength = self.tracker['info']['length']
            self.numPieces = int(math.ceil(float(totalLength)/pieceLength))

        counter = totalLength
        for i in range(self.numPieces):
            if i == self.numPieces-1:
                self.pieces.append(Piece(i, counter, pieceHashes[0:20]))
            else:
                self.pieces.append(Piece(i, pieceLength, pieceHashes[0:20]))
                counter -= pieceLength
                pieceHashes = pieceHashes[20:]

    def chunkToSixBytes(self, peerString):
        """
        Helper function to covert the string to 6 byte chunks.
        4 bytes for the IP address and 2 for the port.
        """
        for i in xrange(0, len(peerString), 6):
            chunk = peerString[i:i+6]
            if len(chunk) < 6:
                raise IndexError("Size of the chunk was not six bytes.")
            yield chunk

    def getPeers(self):
        # TODO: move the self.infoHash to init if we need it later.
        params = {'info_hash': self.infoHash,
                  'peer_id': self.peer_id,
                  'left': str(self.tracker['info']['piece length'])}
        response = requests.get(self.tracker['announce'], params=params)

        if response.status_code > 400:
            errorMsg = ("Failed to connect to tracker.\n"
                        "Status Code: %s \n"
                        "Reason: %s") % (response.status_code, response.reason)
            raise RuntimeError(errorMsg)

        result = bencode.bdecode(response.content)

        for chunk in self.chunkToSixBytes(result['peers']):
            ip = []
            port = None
            for i in range(0, 4):
                ip.append(str(ord(chunk[i])))

            port = ord(chunk[4])*256+ord(chunk[5])
            mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            mySocket.setblocking(0)
            ip = '.'.join(ip)
            peer = Peer(ip, port, mySocket, self.infoHash, self.peer_id)
            self.peers.append(peer)

    def findNextBlock(self, peer):
        pieceFound = None
        for i, piece in enumerate(self.pieces):
            for blockIndex in range(piece.num_blocks):
                if not piece.blockTracker[blockIndex]:
                    return (i, 
                            piece.blocks[blockIndex].offset,
                            piece.blocks[blockIndex].size)
        return None

    def checkIfDoneDownloading(self):
        return all([x.finished for x in self.pieces])

class Peer(object):
    """
    This object contains the information needed about the peer.

    self.ip - The IP address of this peer.
    self.port - Port number for this peer.
    self.choked - sets if the peer is choked or not.
    self.bitField - What pieces the peer has.
    self.socket - Socket object
    self.bufferWrite - Buffer that needs to be sent out to the Peer. When we 
                       instantiate a Peer object, it is automatically filled 
                       with a handshake message.
    self.bufferRead - Buffer that needs to be read and parsed on our end.
    self.handshake - If we sent out a handshake.
    """
    def __init__(self, ip, port, socket, infoHash, peer_id):
        self.ip = ip
        self.port = port
        self.choked = False
        self.bitField = None
        self.sentInterested = False
        self.socket = socket
        self.bufferWrite = self.makeHandshakeMsg(infoHash, peer_id)
        self.bufferRead = ''
        self.handshake = False

    def makeHandshakeMsg(self, infoHash, peer_id):
        pstrlen = '\x13'
        pstr = 'BitTorrent protocol'
        reserved = '\x00\x00\x00\x00\x00\x00\x00\x00'
       
        handshake = pstrlen+pstr+reserved+infoHash+peer_id

        return handshake

    def setBitField(self, payload):
        # TODO: check to see if valid bitfield. Aka the length of the bitfield 
        # matches with the 'on' bits. 
        # COULD BE MALICOUS and you should drop the connection. 
        # Need to calculate the length of the bitfield. otherwise, drop 
        # connection.
        self.bitField = BitArray(bytes=payload)

    def fileno(self):
        return self.socket.fileno()
