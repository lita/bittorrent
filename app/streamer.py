from flask import Flask
from flask import request, Response
import os

app = Flask(__name__)

PATH = os.path.abspath(os.path.dirname(__file__))
PATH = os.path.join(PATH, 'Modern.Family.S05E17.HDTV.x264-2HD.mp4')


@app.route('/stream', methods=['GET'])
def streamMovie():
    def generate():
        with open(PATH, "rb") as f:
            byte = f.read(512)
            while byte:
                yield byte
                byte = f.read(512)

    t = os.stat(PATH)
    sz = str(t.st_size)
    return Response(generate(),mimetype='video/mp4',headers={"Content-Type":"video/mp4","Content-Disposition":"inline","Content-Transfer-Enconding":"binary","Content-Length":sz})

if __name__ == '__main__':
    app.run(debug=True)