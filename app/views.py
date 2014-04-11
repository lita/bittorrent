from flask import render_template, request, flash
from app import app

@app.route('/index')
def index():
    return render_template("index.html")


@app.route('/drop')
def dropzone():
    return render_template("dropzone.html")

@app.route('/upload', methods=['POST'])
def handlefiles():
    if request.method == 'POST':
        file = request.files['file']
        print request.files['file'].filename
        flash('Got File!')

    return render_template("dropzone.html")