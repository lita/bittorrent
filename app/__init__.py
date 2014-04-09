import Queue
import sys
import re

from flask import Flask
from flask import request, Response, render_template

from peers import PeerManager
from reactor import Reactor
import time

import os

TEST = 600000
shared_mem = Queue.PriorityQueue()

PATH = '/Users/litacho/Development/bittorrent/app/test/Modern.Family.S05E17.HDTV.x264-2HD.mp4'


def usage():
    print ("Usage: bittorent <filename>\n\n"
           "filename is the tracker name you wish"
           "to download your file from.")


def initalizeBittorrent():
    global shared_mem
    app = Flask(__name__)
    trackerFile = '[kickass.to]adventure.time.s05e42.hdtv.x264.qcf.eztv.torrent'
    peerMngr = PeerManager(trackerFile, shared_mem)
    app.shared_mem = shared_mem
    app.file_length = peerMngr.totalLength
    app.piece_length = peerMngr.tracker['info']['piece length']
    app.numPieces = peerMngr.numPieces
    app.numBlocks = peerMngr.pieces[0].num_blocks
    app.buffer = ''
    bittorrentThread = Reactor(1, "Thread-1", peerMngr, shared_mem)
    return app, bittorrentThread


app, bittorrentThread = initalizeBittorrent()
bittorrentThread.start()

def generate():
    pieceCur = 0
    while pieceCur < app.numPieces:
        pieceIndex, blocks = app.shared_mem.get()
        if pieceCur != pieceIndex:
            print "Putting stuff back in: %s   %s" % (pieceIndex, pieceCur)
            app.shared_mem.put((pieceIndex, blocks))
            time.sleep(10)
            continue
        print "Piece Num: %d Num of stuff in PQueue: %d" % (pieceIndex, app.shared_mem._qsize())
        #app.buffer += blocks
        yield ''.join(blocks)
        pieceCur += 1

def generate2():
    with open(PATH, 'rb') as f:
        byte = f.read(2**14)
        while byte:
            yield byte
            byte = f.read(2**14)

def get_data(byte1, length):
    print "data"
    #import pudb; pudb.set_trace(); 
    for i in xrange(byte1, len(app.buffer), 2**14):
        yield app.buffer[i:i+2**14]

    if len(app.buffer) < byte1+length:
        for i in generate():
            yield i

@app.route('/stream')
def streamMovie():
    print request.headers
    sz = str(app.file_length)
    print sz
    t = os.stat(PATH)
    s = str(t.st_size)
    print s
    return Response(generate(),mimetype='video/mp4',headers={"Content-Type":"video/mp4","Content-Disposition":"inline","Content-Transfer-Enconding":"binary","Content-Length":s})

"""
@app.route('/stream', methods=['GET'])
def streamMovie():
    #import pudb; pudb.set_trace(); app.file_length = 10000
    #t = os.stat(PATH); app.file_length = t.st_size
    #import pudb; pudb.set_trace(); 
    print request.headers

    headers = {}    
    range_header = request.headers.get('Range', None)
    if not range_header:
        headers['Content-Length'] = str(app.file_length)
        headers['Content-Type'] = 'video/mp4'
        return Response(generate(),headers=headers, direct_passthrough=True)

    byte1, byte2 = 0, None
    
    m = re.search('(\d+)-(\d*)', range_header)
    g = m.groups()
    
    if g[0]: byte1 = int(g[0])
    if g[1]: byte2 = int(g[1])


    if not byte2:
        byte2 = app.file_length - byte1 - 1

    length = byte2 - byte1 + 1
       
    
    with open(PATH, 'rb') as f:
        f.seek(byte1)
        data = f.read(length)
    
    headers = {'Content-Length': str(app.file_length)}
    rv =  Response(get_data(byte1,length), 206, mimetype='video/mp4', headers=headers)

    rv.headers.add('Accept-Ranges', 'bytes')
    rv.headers.add('Content-Type', 'video/mp4')
    rv.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(byte1, byte2, app.file_length))
    rv.headers.add('Connection', 'keep-alive')
   
    return rv
"""

@app.route('/index')
def index():
    return render_template("index.html")


