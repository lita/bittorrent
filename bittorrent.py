import bencode
import requests
import hashlib
import socket
import pdb

class Peers(object):
    def __init__(self, trackerFile):
        self.peers = {}
        self.peer_id = '-lita38470993824756-'
        tracker = bencode.bdecode(open(trackerFile,'rb').read())
        self.infoHash = hashlib.sha1(bencode.bencode(tracker['info'])).digest()
        peersString = self.getPeers(tracker)
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
            self.peers['.'.join(ip)] = port

    def getPeers(self, tracker):
        # TODO: move the self.infoHash to init if we need it later.
        params = {'info_hash': self.infoHash,
                  'peer_id': self.peer_id,
                  'left': str(tracker['info']['piece length'])}

        response = requests.get(tracker['announce'], params=params)

        if response.status_code > 400:
            errorMsg = ("Failed to connect to tracker.\n"
                        "Status Code: %s \n"
                        "Reason: %s") % (response.status_code, response.reason)
            raise RuntimeError(errorMsg)

        result = bencode.bdecode(response.content)
        return result['peers']

def makeHandshakeMsg(peers):
    pstrlen = '\x13'
    pstr = 'BitTorrent protocol'
    reserved = '\x00\x00\x00\x00\x00\x00\x00\x00'
    infoHash = peers.infoHash
    peer_id = '-lita38470993824756-'

    handshake = pstrlen+pstr+reserved+infoHash+peer_id

    return handshake

def checkValidPeer(response, peers):
    headerSize = 28 # This is just the pstrlen+pstr+reserved
    responseInfoHash = response[28:28+len(peers.infoHash)]
    
    if responseInfoHash == peers.infoHash:
        return True
    else:
        return False

def connectToPeers(peers):
    header_size = 48
    for ip in peers.peers.keys():
        port = peers.peers[ip]
        mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mySocket.settimeout(3)
        try:
            mySocket.connect((ip, port))
        except socket.timeout:
            print "Connection Time out. IP %s Port: %s " % (ip, port)
            mySocket.close()
            continue
        except socket.error as err:
            print "Failed connection. IP: %s Port: %s" % (ip, port)
            print "Error: %s" % err
            mySocket.close()
            continue

        handshake = makeHandshakeMsg(peers)
        mySocket.send(handshake)
        response = mySocket.recv(1028)
        print "Conncted to IP: %s Port: %s" % (ip, port)

        if checkValidPeer(response, peers):
            return mySocket
        else:
            print "Info Hash does not match. Moving to next peer..."
            mySocket.close()
            continue

def main():
    trackerFile = 'AllAboutInternetMarketing newsletters sets Free download 2013 [mininova].torrent'
    peers = Peers(trackerFile)
    mySocket = connectToPeers(peers)
    print "PROGRESS!"



if __name__ == "__main__":
    main()
