import hashlib
import pdb
import socket
import struct
import math
import sys
import os

from bitstring import BitArray
import bencode
import requests

from peers import PeerManager
from pieces import Piece

class BittorrentParser(object):
    """
    This is the heart of the program. The BittorrentParser sends and recieves packets
    from the peer connected. It parses the packet to the Bittorrent protocal depending
    on the message code. Then sends a 'request' message to get more data till the file
    is completely downloaded.
    """
   
    def __init__(self, socket, message, peers):
        self.socket = socket
        self.buffer = message
        self.sentInterested = False
        self.pieces = []
        self.generatePieces(peers)
        self.bitField = BitArray(len(self.pieces))
]
    def generatePieces(self, peers):

        print "Initalizing..."

        files = peers.tracker['info']['files']
        totalLength = 0
        pieceHashes = peers.tracker['info']['pieces']
        pieceLength = peers.tracker['info']['piece length']
        totalLength = sum([file['length'] for file in files])
        self.numPieces =  int(math.ceil(float(totalLength)/pieceLength))
        counter = totalLength
        for i in range(self.numPieces):
            if i == self.numPieces-1:
                self.pieces.append(Piece(i, counter, pieceHashes[0:20]))
            else:
                self.pieces.append(Piece(i, pieceLength, pieceHashes[0:20]))
                counter -= self.pieceLength
                pieceHashes = pieceHashes[20:]

    def convertBytesToDecimal(self, headerBytes, power):
        size = 0
        for ch in headerBytes:
            size += int(ord(ch))*256**power
            power -= 1
        return size

    def handleBitfield(self, payload):
        # TODO: check to see if valid bitfield. Aka the length of the bitfield matches with the 'on' bits. 
        # COULD BE MALICOUS and you should drop the connection. 
        self.bitField = BitArray(bytes=payload)

    def handleHave(self, payload):
        index = self.convertBytesToDecimal(payload, 3)
        print "Handling Have"
        print "Index: %d" % index
        self.bitField[index] = True

    def parse_message(self):
        while self.buffer:
            msgSize = self.convertBytesToDecimal(self.buffer[0:4], 3)
            msgCode = int(ord(self.buffer[4:5]))
            payload = self.buffer[5:4+msgSize]

            if len(payload) < msgSize-1:
                self.buffer = self.buffer + self.socket.recv(1028)
                payload = self.buffer[5:4+msgSize]

            self.buffer = self.buffer[msgSize+4:]

            return (msgSize, payload, msgCode)
            

    def makeInterestedMessage(self):
        interested = '\x00\x00\x00\x01\x02'

        return interested

    def findNextBlock(self):
        for i in range(len(self.pieces)):
            if self.bitField[i]:
                piece = self.pieces[i]
                for j in range(piece.num_blocks):
                    if not piece.bitField[j]:
                        return (i, piece.blocks[j].offset, piece.blocks[j].size)
        return None

    def sendRequest(self, index, offset, length):
        header = struct.pack('>I', 13)
        id = '\x06'
        index = struct.pack('>I', index)
        offset = struct.pack('>I', offset)
        length = struct.pack('>I', length)
        request = header + id + index + offset + length
        self.socket.send(request)
        self.buffer = self.socket.recv(2**14)

    def process_message(self):
        while self.buffer:
            msgSize = self.convertBytesToDecimal(self.buffer[0:4], 3)
            msgCode = int(ord(self.buffer[4:5]))
            payload = self.buffer[5:4+msgSize]

            while len(payload) < msgSize-1:
                self.buffer = self.buffer + self.socket.recv(2**14)
                payload = self.buffer[5:4+msgSize]

            self.buffer = self.buffer[msgSize+4:]

            if not msgCode:
                # Keep Alive
                self.buffer += self.socket.recv(2**14)
                continue

            elif msgCode == 0:
                # Choked
                self.buffer += self.socket.recv(2**14)
                continue
            elif msgCode == 1:
                # Unchoked! send request
                print "Unchoked! Downloading file.",
                nextBlock = self.findNextBlock()
                if not nextBlock:
                    # Nothing left to process
                    return
                index, offset, length = nextBlock
                self.sendRequest(index, offset, length)
            elif msgCode == 4:
                self.handleHave(payload)
            elif msgCode == 5:
                self.handleBitfield(payload)
            elif msgCode == 7:
                print ".",
                sys.stdout.flush()

                index = self.convertBytesToDecimal(payload[0:4], 3)
                offset = self.convertBytesToDecimal(payload[4:8], 3)
                data = payload[8:]
                piece = self.pieces[index]

                piece.addBlock(offset, data)
                if piece.finished:
                    self.bitField[index] = 0
                nextBlock = self.findNextBlock()
                if not nextBlock:
                    # No more pieces to download
                    return
                index, offset, length = nextBlock
                self.sendRequest(index, offset, length)

            if not self.buffer and not self.sentInterested:
                print ("Bitfield initalized. "
                       "Sending peer we are interested...")
                self.socket.send(self.makeInterestedMessage())
                self.buffer += self.socket.recv(2**14)
                self.sentInterested=True

def generateMoreData(myBuffer, pieces):
    for piece in pieces:
        if piece.block:
            myBuffer += piece.block
            yield myBuffer
        else:
            raise ValueError('Pieces was corrupted. Did not download piece properly.')

def writeToFile(files, dirs, pieces):
    bufferGenerator = None
    myBuffer = ''
    if not os.path.exists('./' + dirs):
        os.makedirs('./'+dirs)
    for f in files:
        fileObj = open('./' + dirs + '/' + f['path'][0], 'wb')
        length = f['length']

        if not bufferGenerator:
            bufferGenerator = generateMoreData(myBuffer, pieces)

        while length > len(myBuffer):
            myBuffer = next(bufferGenerator)

        fileObj.write(myBuffer[:length])
        myBuffer = myBuffer[length:]
        fileObj.close()

def usage():
    print ("Usage: bittorent <filename>\n\n"
           "filename is the tracker name you wish"
           "to download your file from.")

def main():
    args = sys.argv[1:]
    if '-h' in args or '--help' in args:
        usage()
        sys.exit(2)

    trackerFile = sys.argv[1]
    peers = PeerManager(trackerFile)
    mySocket, message = peers.connectToPeers()
    if mySocket==None:
        raise RuntimeError("could not find peer")
    bittorrentParser = BittorrentParser(mySocket, message, peers)
    bittorrentParser.process_message()
    print "Writing to File..."
    writeToFile(peers.tracker['info']['files'],
                peers.tracker['info']['name'],
                bittorrentParser.pieces)
    print "Done!"

if __name__ == "__main__":
    main()
