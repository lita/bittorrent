import socket
import select
import sys
import pdb

import bittorrent
from peers import PeerManager



class Reactor(object):
    """ 
    This is our event loop that makes our program asynchronous. The program
    keeps looping until the file is fully downloaded.
    """
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

    def removePeer(self, peer):
        if peer in self.peerMngr.peers:
            self.peerMngr.peers.remove(peer)

    def run(self):
        while not self.peerMngr.checkIfDoneDownloading():
            write = [x for x in self.peerMngr.peers if x.bufferWrite != '']
            read = self.peerMngr.peers[:]
            readList, writeList, err = select.select(read, write, [])
            
            for peer in writeList:
                sendMsg = peer.bufferWrite
                try:
                    peer.socket.send(sendMsg)
                except socket.error as err:
                    print err
                    self.removePeer(peer)
                    continue 
                peer.bufferWrite = ''

            for peer in readList:
                try:
                    peer.bufferRead += peer.socket.recv(1028)
                except socket.error as err:
                    print err
                    self.removePeer(peer)
                    continue
                result = bittorrent.process_message(peer, self.peerMngr)
                if not result:
                    # Something went wrong with peer. Discconnect
                    peer.socket.close()
                    self.removePeer(peer)

            if len(self.peerMngr.peers) <= 0:
                raise Exception("NO MO RE PEERS")

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
    bittorrent.write(peerMngr.tracker['info'], peerMngr.pieces)

if __name__ == "__main__":
    main()
