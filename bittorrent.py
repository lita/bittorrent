import hashlib
]import socket
import struct
import math
import sys
import os

from bitstring import BitArray
import bencode
import requests

from peers import PeerManager
from pieces import Piece
from reactor import Reactor

# TODO make the parser stateless and a parser for each object 

def checkValidPeer(response, infoHash):
    responseInfoHash = response[HEADER_SIZE:HEADER_SIZE+len(self.infoHash)]
    
    if responseInfoHash == infoHash:
        message = response[HEADER_SIZE+len(infoHash)+20:]
        print "Handshake Valid"
        return message
    else:
        raise ValueError('InfoHash does not mach')

def convertBytesToDecimal(headerBytes, power):
    size = 0
    for ch in headerBytes:
        size += int(ord(ch))*256**power
        power -= 1
    return msgSize
    
    """
    def handleBitfield(self, payload):
        # TODO: check to see if valid bitfield. Aka the length of the bitfield matches with the 'on' bits. 
        # COULD BE MALICOUS and you should drop the connection. 
        self.bitField = BitArray(bytes=payload)
    """

def handleHave(peer, payload):
    index = self.convertBytesToDecimal(payload, 3)
    print "Handling Have"
    print "Index: %d" % index
    peer.bitField[index] = True

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
            

def makeInterestedMessage():
    interested = '\x00\x00\x00\x01\x02'

    return interested

def findNextBlock(peerMngr, peersConnected):
    for i in range(len(peerMngr.pieces)):
        if not peerMngr.bitField[i]:
            piece = peerMngr.pieces[i]
            foundPeer = None
            for peer in peersConnected:
                if peer.bitfield[i]:
                    foundPeer = peer
                    break
            for j in range(piece.num_blocks):
                if not piece.bitField[j]:
                    return (i, 
                            piece.blocks[j].offset, 
                            piece.blocks[j].size, 
                            foundPeer)
    return None

    def sendRequest(peer, index, offset, length):
        header = struct.pack('>I', 13)
        id = '\x06'
        index = struct.pack('>I', index)
        offset = struct.pack('>I', offset)
        length = struct.pack('>I', length)
        request = header + id + index + offset + length
        self.socket.send(request)
        self.buffer = self.socket.recv(2**14)

    def process_message(peer, peerMngr, peersConnected):
        while peer.bufferRead:
            msgSize = self.convertBytesToDecimal(peer.bufferRead[0:4], 3)
            msgCode = int(ord(peer.bufferRead[4:5]))
            payload = peer.bufferRead[5:4+msgSize]
            if len(payload) < msgSize-1:
                # Message is not complete. Return
                return
            peer.bufferRead = peer.bufferRead[msgSize+4:]
            if not msgCode:
                # Keep Alive. Keep the connection alive.
                continue
            elif msgCode == 0:
                # Choked
                peer.choked = True
                continue
            elif msgCode == 1:
                # Unchoked! send request
                print "Unchoked! Downloading file.",
                peer.choked = False
                nextBlock = findNextBlock(peerMngr, peersConnected)
                if not nextBlock:
                    # Nothing left to process. Need to return a done statment
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

            if not peer.bufferRead and not self.sentInterested:
                print ("Bitfield initalized. "
                       "Sending peer we are interested...")
                self.socket.send(self.makeInterestedMessage())
                peer.bufferRead += self.socket.recv(2**14)
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
    peerMgnr = PeerManager(trackerFile)
    reactor = Reactor(peerMgnr)
    """
    torrentParser = BittorrentParser(peerMngr)


    bittorrentParser = BittorrentParser(mySocket, message, peers)
    bittorrentParser.process_message()
    print "Writing to File..."
    writeToFile(peers.tracker['info']['files'],
                peers.tracker['info']['name'],
                bittorrentParser.pieces)
    print "Done!"
    """

if __name__ == "__main__":
    main()
