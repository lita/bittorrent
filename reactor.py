import socket
import select
import sys
import multiprocessing
import logging

import bittorrent
from peers import PeerManager

class Reactor(multiprocessing.Process):
    """ 
    This is our event loop that makes our program asynchronous. The program
    keeps looping until the file is fully downloaded.
    """
    def __init__(self, threadID, name, peerMngr, shared_mem, config):
        multiprocessing.Process.__init__(self)
        self.threadID = threadID
        self.name = name
        self.shared_mem = shared_mem
        self.stream = False
        if config['DEBUG']:
            logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        elif config['INFO']:
            logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        if config['STREAMING']:
            self.stream = True
        self.peerMngr = peerMngr

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
        self.connect()
        while not self.peerMngr.checkIfDoneDownloading():
            write = [x for x in self.peerMngr.peers if x.bufferWrite != '']
            read = self.peerMngr.peers[:]
            readList, writeList, err = select.select(read, write, [])
            
            for peer in writeList:
                sendMsg = peer.bufferWrite
                try:
                    peer.socket.send(sendMsg)
                except socket.error as err:
                    logging.debug(err)
                    self.removePeer(peer)
                    continue 
                peer.bufferWrite = ''

            for peer in readList:
                try:
                    peer.bufferRead += peer.socket.recv(1028)
                except socket.error as err:
                    logging.debug(err)
                    self.removePeer(peer)
                    continue
                result = bittorrent.process_message(peer, self.peerMngr, self.shared_mem)
                if not result:
                    # Something went wrong with peer. Discconnect
                    peer.socket.close()
                    self.removePeer(peer)

            if len(self.peerMngr.peers) <= 0:
                raise Exception("NO MO RE PEERS")
        if not self.stream:
            bittorrent.write(self.peerMngr.tracker['info'], self.shared_mem)       
        return
