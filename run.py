import sys
from peers import PeerManager
from reactor import Reactor
import Queue


def main():
    shared_mem=Queue.PriorityQueue()
    trackerFile = sys.argv[1]
    peerMngr = PeerManager(trackerFile, shared_mem)
    bittorrentThread = Reactor(1, "Thread-1", peerMngr, shared_mem)
    bittorrentThread.run()

if __name__ == '__main__':
    main()