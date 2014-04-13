from  multiprocessing import Queue
from Queue import PriorityQueue
import sys
import re
import json
import time
import os
import logging
import uuid

from flask import Flask
from flask import request, Response, redirect
from flask import render_template, config, flash, url_for
from flask import session

from peers import PeerManager
from reactor import Reactor
import app.bt_session as bt_session


logging = logging.getLogger('flask')
BOLD_SEQ = "\033[1m"

OKGREEN = '\033[92m'
RESET_SEQ = "\033[0m"

TEST = 600000

PATH = '/Users/litacho/Development/bittorrent/app/test/Modern.Family.S05E17.HDTV.x264-2HD.mp4'

def usage():
    print ("Usage: bittorent <filename>\n\n"
           "filename is the tracker name you wish"
           "to download your file from.")

def initalizeBittorrent(fileStorage):
    bt_session.new()
    bt_session.set('shared_mem', Queue())
    bt_session.set('buffer', PriorityQueue())
    peerMngr = PeerManager(stream=fileStorage)
    session['file_length'] = peerMngr.totalLength
    session['numPieces'] = peerMngr.numPieces
    bt_session.set('bt', Reactor(1, "Thread-1", peerMngr, bt_session.get('shared_mem'), app.config))
    bt_session.get('bt').start()

#app, bittorrentThread = initalizeBittorrent()
#bittorrentThread.start()

app = Flask(__name__)
app.config.from_object('config')
bittorrentThread = None

def generate(numPieces, buffer, shared_mem):
    pieceCur = 0
    while pieceCur < numPieces:
        buffer.put(shared_mem.get())
        #bt_session.get('buffer').put(bt_session.get('shared_mem').get())
        pieceIndex, blocks = buffer.get()
        if pieceCur != pieceIndex:
            logging.info("Putting stuff back in: %s   %s" % (pieceIndex, pieceCur))
            buffer.put((pieceIndex, blocks))
            time.sleep(10)
            continue
        logging.info((OKGREEN + BOLD_SEQ + "Piece Num: %d Num of stuff in PQueue: %d " + RESET_SEQ) % (pieceIndex, buffer._qsize()))
        #app.buffer += blocks
        yield ''.join(blocks)
        pieceCur += 1

def generate2():
    with open(PATH, 'rb') as f:
        byte = f.read(2**14)
        while byte:
            yield byte
            byte = f.read(2**14)

@app.route('/stream')
def streamMovie():
    print request.headers
    file_length = str(session['file_length'])
    return Response(generate(session['numPieces'], bt_session.get('buffer'), bt_session.get('shared_mem')),mimetype='video/mp4',headers={"Content-Type":"video/mp4","Content-Disposition":"inline","Content-Transfer-Enconding":"binary","Content-Length": file_length})


@app.route('/index')
def index():
    if  bt_session.get('bt') is None:
        flash('Torrent file failed')
        return redirect('/drop')
    elif 'file_length' not in session:
        index()
    return render_template("index.html")

@app.route('/drop')
def dropzone():
    return render_template("dropzone.html")

@app.route('/upload', methods=['POST'])
def handlefiles():
    if request.method == 'POST':
        torrentStream = request.files['file']
        if torrentStream.filename.endswith('.torrent'):
            initalizeBittorrent(torrentStream)
            return json.dumps({'site':'/index'})
        else:
            flash("Error! File was not a valid torrent file! Try again!")
            return json.dumps({'site':'/drop'})

"""
TODO: Handle 206 requests in order for users to scrub, pause and play video. 
Here is like... a starting point..

def get_data(byte1, length):
    print "data"
    #import pudb; pudb.set_trace(); 
    for i in xrange(byte1, len(app.buffer), 2**14):
        yield app.buffer[i:i+2**14]

    if len(app.buffer) < byte1+length:
        for i in generate():
            yield i

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
