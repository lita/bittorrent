
import hashlib
import socket

import bencode
import requests

HEADER_SIZE = 28 # This is just the pstrlen+pstr+reserved

class PeerManager(object):
    """
    Holds the tracker information and the list of ip addresses and ports.
    """
    def __init__(self, trackerFile):
        self.peers = []
        self.peer_id = '-lita38470993887523-'
        self.tracker = bencode.bdecode(open(trackerFile,'rb').read())
        self.infoHash = hashlib.sha1(bencode.bencode(self.tracker['info'])).digest()
        peersString = self.getPeers()
        self.peersString = peersString
        self.parseBinaryModelToString(peersString)

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

    def parseBinaryModelToString(self, peersString):
        """
        Converts the binary model, which is the string in
        hex, into an IP address and port number
        """
        for chunk in self.chunkToSixBytes(peersString):
            ip = []
            port = None
            for i in range(0, 4):
                ip.append(str(ord(chunk[i])))

            port = ord(chunk[4])*256+ord(chunk[5])
            peer = Peer('.'.join(ip), port)
            self.peers.append(peer)

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
        return result['peers']

    def makeHandshakeMsg(self):
        pstrlen = '\x13'
        pstr = 'BitTorrent protocol'
        reserved = '\x00\x00\x00\x00\x00\x00\x00\x00'
        peer_id = '-lita38470993824756-'

        handshake = pstrlen+pstr+reserved+self.infoHash+peer_id

        return handshake

    def checkValidPeer(self, response):
        responseInfoHash = response[HEADER_SIZE:HEADER_SIZE+len(self.infoHash)]
        
        if responseInfoHash == self.infoHash:
            message = response[HEADER_SIZE+len(self.infoHash)+20:]

            return message
        else:
            return None

    def connectToPeers(self):
        while self.peers:
            peer = self.peers.pop()
            mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            mySocket.settimeout(5)
            try:
                mySocket.connect((peer.ip, peer.port))
            except socket.timeout:
                print "Connection Time out. IP %s Port: %s " % (peer.ip, peer.port)
                mySocket.close()
                continue
            except socket.error as err:
                print "Failed connection. IP: %s Port: %s" % (peer.ip, peer.port)
                print "Error: %s" % err
                mySocket.close()
                continue

            handshake = self.makeHandshakeMsg()
            mySocket.send(handshake)
            
            try:
                response = mySocket.recv(1028)
            except socket.error as err:
                print "Failed connection. IP: %s Port: %s" %  (peer.ip, peer.port)
                print "Error: %s" % err
                mySocket.close()
                continue            

            print "Conncted to IP: %s Port: %s" %  (peer.ip, peer.port)
            message = self.checkValidPeer(response)
            if message:
                print "Handshake Valid"
                return (mySocket, message)
            else:
                print "Info Hash does not match. Moving to next peer..."
                mySocket.close()
                continue
            mySocket.close()
        return(None, None)

class Peer(object):
    """
    Peer object
    """
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

