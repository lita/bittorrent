import Queue
import sys
import re

from flask import Flask
from flask import request, Response, render_template

from peers import PeerManager
from reactor import Reactor
import time

import os

shared_mem = Queue.PriorityQueue()

PATH = 'Modern.Family.S05E17.HDTV.x264-2HD.mp4'

PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), PATH)

def usage():
    print ("Usage: bittorent <filename>\n\n"
           "filename is the tracker name you wish"
           "to download your file from.")

def initalizeBittorrent():
    global shared_mem
    app = Flask(__name__)
    trackerFile = 'Four.Eyed.Monsters.HQ.x264-VODO [mininova].torrent'
    peerMngr = PeerManager(trackerFile, shared_mem)
    app.shared_mem = shared_mem
    app.file_length = peerMngr.totalLength
    app.numPieces = peerMngr.numPieces
    app.numBlocks = peerMngr.pieces[0].num_blocks
    bittorrentThread = Reactor(1, "Thread-1", peerMngr, shared_mem)
    bittorrentThread.start()
    return app

app = initalizeBittorrent()

pieceCur = 0
def generate():
    global pieceCur
    while pieceCur < app.numPieces:
        pieceIndex, blocks = app.shared_mem.get()
        if pieceCur != pieceIndex:
            print "Putting stuff back in: %s   %s" % (pieceIndex, pieceCur)
            app.shared_mem.put((pieceIndex, blocks))
            time.sleep(10)
            continue
        print "Piece Num: %d Num of stuff in PQueue: %d" % (pieceIndex, app.shared_mem._qsize())
        for block in blocks:
            yield block.data
        pieceCur += 1

def generate2():
    with open(PATH, 'rb') as f:
        byte = f.read(2**14)
        while byte:
            yield byte
            byte = f.read(2**14)

@app.route('/stream', methods=['GET'])
def streamMovie():
    #import pudb; pudb.set_trace(); app.file_length = 10000
    #t = os.stat(PATH); app.file_length = t.st_size

    print request.headers
    headers={"Content-Type":"video/mp4"}
    """
    range_header = request.headers.get('Range', None)
    if not range_header:
        headers['Content-Length'] = str(app.file_length)
        return Response(generate(),headers=headers, direct_passthrough=True)

    byte1, byte2 = 0, None
    
    m = re.search('(\d+)-(\d*)', range_header)
    g = m.groups()
    
    if g[0]: byte1 = int(g[0])
    if g[1]: byte2 = int(g[1])

    length = app.file_length - byte1
    if byte2 is not None:
        length = byte2 - byte1
    """
    headers['Content-Length'] = str(app.file_length)
    #headers['Content-Range'] = 'bytes {0}-{1}/{2}'.format(byte1, byte1 + length - 1, app.file_length)

    rv =  Response(generate(),
                    direct_passthrough=True, 
                    mimetype='video/mp4',
                    headers=headers)
    return rv

@app.route('/index')
def index():
    return render_template("index.html")

