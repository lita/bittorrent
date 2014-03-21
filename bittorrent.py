import hashlib
import struct
import math
import sys
import os

from bitstring import BitArray
import bencode
import requests

import pdb

HEADER_SIZE = 28 # This is just the pstrlen+pstr+reserved
# TODO make the parser stateless and a parser for each object 

def checkValidPeer(peer, infoHash):
    """
    Check to see if the info hash from the peer matches with the one we have 
    from the .torrent file.
    """
    peerInfoHash = peer.bufferRead[HEADER_SIZE:HEADER_SIZE+len(infoHash)]
    
    if peerInfoHash == infoHash:
        peer.bufferRead = peer.bufferRead[HEADER_SIZE+len(infoHash)+20:]
        peer.handshake = True
        print "Handshake Valid"
        return True
    else:
        return False

def convertBytesToDecimal(headerBytes, power):
    size = 0
    for ch in headerBytes:
        size += int(ord(ch))*256**power
        power -= 1
    return size

def handleHave(peer, payload):
    index = convertBytesToDecimal(payload, 3)
    print "Handling Have"
    print "Index: %d" % index
    peer.bitField[index] = True

def makeInterestedMessage():
    interested = '\x00\x00\x00\x01\x02'

    return interested

def findNextBlock(peer, peerMngr):
    piece = None
    index = -1
    for i in range(len(peerMngr.pieceTracker)):
        if not peerMngr.pieceTracker[i] and not i in peerMngr.piecesInProgress:
            # Check to see if peer has this piece
            if peer.bitField[i]:
                piece = peerMngr.pieces[i]
                index = i
                # Put it in the list of currently running
                peerMngr.piecesInProgress.append(i)
                peer.pieceDownloading = i
                break
    if not piece:
        # Peer does not have pieces we want
        return None

    for j in range(piece.num_blocks):
        if not piece.bitField[j]:
            return (index, piece.blocks[j].offset, piece.blocks[j].size)

def sendRequest(index, offset, length):
    header = struct.pack('>I', 13)
    id = '\x06'
    index = struct.pack('>I', index)
    offset = struct.pack('>I', offset)
    length = struct.pack('>I', length)
    request = header + id + index + offset + length
    return request

def process_message(peer, peerMngr):
    while len(peer.bufferRead) > 3:
        print "Ip: " + peer.ip
        print "Buffer: " + str(repr(peer.bufferRead))
        if not peer.handshake:
            if not checkValidPeer(peer, peerMngr.infoHash):
                return False
            elif len(peer.bufferRead) < 4:
                return True

        msgSize = convertBytesToDecimal(peer.bufferRead[0:4], 3)
        if len(peer.bufferRead) == 4:
            if msgSize == '\x00\x00\x00\x00':
                # Keep alive
                return True
            return True 
        try:
            msgCode = int(ord(peer.bufferRead[4:5]))
        except:
            pdb.set_trace()
        
        payload = peer.bufferRead[5:4+msgSize]

        print "MsgCode: " + str(msgCode)

        if len(payload) < msgSize-1:
            # Message is not complete. Return
            return True

        peer.bufferRead = peer.bufferRead[msgSize+4:]
        print "New Buffer: " + str(repr(peer.bufferRead))
        print " "
        
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
            nextBlock = findNextBlock(peer, peerMngr)
            if not nextBlock:
                # Couldn't find a block. Return False
                return False
            index, offset, length = nextBlock
            peer.bufferWrite += sendRequest(index, offset, length)
        elif msgCode == 4:
            handleHave(peer, payload)
        elif msgCode == 5:
            peer.setBitField(payload)
        elif msgCode == 7:
            print ".",
            sys.stdout.flush()

            index = convertBytesToDecimal(payload[0:4], 3)
            offset = convertBytesToDecimal(payload[4:8], 3)
            data = payload[8:]
            piece = peerMngr.pieces[index]

            piece.addBlock(offset, data)
            if piece.finished and not piece.hashGood:
                piece.reset()
                return False
            if piece.finished and piece.hashGood:
                peerMngr.pieceTracker[index] = 1
                peerMngr.piecesInProgress.remove(index)
            nextBlock = findNextBlock(peer, peerMngr)
            if not nextBlock:
                removePiece = peer.pieceDownloading 
                if removePiece in peerMngr.piecesInProgress:
                    peerMngr.piecesInProgress.remove(removePiece)
                return False
            index, offset, length = nextBlock
            peer.bufferWrite = sendRequest(index, offset, length)

        if not peer.sentInterested:
            print ("Bitfield initalized. "
                   "Sending peer we are interested...")
            peer.bufferWrite = makeInterestedMessage()
            peer.sentInterested = True
    return True

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


