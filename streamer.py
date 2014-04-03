from flask import Flask
from flask import request, Response, render_template
import os

app = Flask(__name__)

PATH = os.path.abspath(os.path.dirname(__file__))
PATH = os.path.join(PATH, 'Modern.Family.S05E17.HDTV.x264-2HD.mp4')

"""
@app.route('/stream', methods=['GET'])
def streamMovie():
    print PATH
    print "THIS IS HERE"
    pdb.set_trace()
    def generate():
        with open(PATH, "rb") as f:
            byte = f.read(512)
            while byte:
                yield byte
                byte = f.read(512)

    t = os.stat(PATH)
    sz = str(t.st_size)
    return Response(generate(),mimetype='video/mp4',headers={"Accept-Ranges": "bytes","Content-Type":"video/mp4","Content-Disposition":"inline","Content-Transfer-Enconding":"binary","Content-Length":sz})

@app.route('/index')
def index():
    return render_template("index.html")
"""

@app.route('/stream', methods=['GET'])
def streamMovie():
    def generate():
        pieceCur = 0
        pieceSent = 0
        while pieceSent < app.file_length:
            try:
                index, piece = app.shared_mem.get()
            except TypeError:
                pdb.set_trace()

            if index != pieceCur:
                app.shared_mem.put((index,piece))
                continue
            for block in piece.blocks:
                data = block.data
                while data:
                    yield data[0:32]
                    data = data[32:]
                pieceSent += 2**14
    headers={"Accept-Ranges": "bytes",
             "Content-Type":"video/mp4",
             "Content-Disposition":"inline",
             "Content-Transfer-Enconding":"binary",
             "Content-Length":app.file_length}
    print "QUEUE SIZE" + str(app.shared_mem.qsize())
    return Response(generate(),mimetype='video/mp4',headers=headers)