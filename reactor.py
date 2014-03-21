import socket
import select
import sys
import pdb

import bittorrent
from peers import PeerManager



class Reactor(object):
    def __init__(self, peerMngr):
        self.peerMngr = peerMngr
        self.connect()
        self.run()


    def connect(self):
        for peer in self.peerMngr.peers:
            try:
                peer.socket.connect((peer.ip, peer.port))
            except socket.error:
                # We are going to ignore the error, since we are turing blocking
                # off. Since we are returning before connect can return a 
                # message, it will throw an error. 
                pass


        """
        # Hard-coded to connect to 10 peers for now. TODO: make it a variable.
        while len(self.peersConnented) < 10 and len(peers) > 0:
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
        """

    def removePeer(self, peer):
        if peer in self.peerMngr.peers:
            self.peerMngr.peers.remove(peer)

    def run(self):
        while True:
            write = [x for x in self.peerMngr.peers if x.bufferWrite != '']
            read = self.peerMngr.peers[:]
            readList, writeList, err = select.select(read, write, [])

            print readList
            
            for peer in writeList:
                sendMsg = peer.bufferWrite
                peer.bufferWrite = ''
                try:
                    peer.socket.send(sendMsg)
                except socket.error as err:
                    self.removePeer(peer)
                    continue 

            for peer in readList:
                try:
                    peer.bufferRead += peer.socket.recv(1028)
                except socket.error as err:
                    continue
                result = bittorrent.process_message(peer, self.peerMngr)
                if not result:
                    # Something went wrong with peer. Discconnect
                    peer.socket.close()
                    self.removePeer(peer)

            if all(self.peerMngr.pieceTracker):
                break

            print self.peerMngr.pieceTracker
            if len(self.peerMngr.peers) <= 0:
                raise Exception("NO MORE PEERS")

        return

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
    peerMngr = PeerManager(trackerFile)
    reactor = Reactor(peerMngr)
    print "Writing to File..."
    bittorrent.writeToFile(peerMngr.tracker['info']['files'],
                           peerMngr.tracker['info']['name'],
                           peerMngr.pieces)
    print "Done!"

if __name__ == "__main__":
    main()
