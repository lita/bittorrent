import socket
import select

HEADER_SIZE = 28 # This is just the pstrlen+pstr+reserved

class Reactor(object):
    def __init__(self, peerMngr):
        self.peersConnented = []
        self.peerMngr = peerMngr
        self.connect()
        self.run()


    def connect(self):
        peers = self.peerMngr.peers

        # Hard-coded to connect to 10 peers for now. TODO: make it a variable.
        while len(self.peersConnented) < 10 and len(peers > 0):
            peer = peers.pop()

            try:
                peer.socket.connect((peer.ip, peer.port))
            except socket.error:
                # We are going to ignore the error, since we are turing blocking
                # off. Since we are returning before connect can return a 
                # message, it will throw an error. 
                pass
            self.peersConnented.append(peer)
        else:
            if len(self.peersConnented) == 0:
                raise Exception('Cannot connect to any peers')

    def run(self):
        while True:
            write = [x for x in self.peersConnented if x.bufferWrite != '']
            readList, writeList, err = select.select(self.peersConnented, 
                                                     write, [])
            for peer in readList:
                peer.bufferRead += peer.socket.recv(1028)

            for peer in writeList:
                sendMsg = peer.bufferWrite
                peer.bufferWrite = ''
                peer.socket.send(sendMsg)

            for errorSockets in err:
                errorSockets.socket.close()

            

        
        exit(0)

"""
            select
            peer = peerMngr.peers.pop()
            if not peer.handshake:
                try:
                    infoHash = peerMngr.infoHash
                    peer_id = peerMngr.peer_id
                    peer.socket.send(self.makeHandshakeMsg(infoHash, peer_id))
                    response = peer.socket.recv(1028)
                    message = self.checkValidPeer(response, infoHash)
                except peer.socket.error as err:
                    peer.socket.close()
                    continue
                except ValueError as err:
                    print err
                    peer.socket.close()
                    continue
            parser.initalizeBuffer(message)
"""

