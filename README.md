==========
Lita's Bittorrent Streamer
==========
This program is written on top of my Bittorrent Client. The bare bones of my 
Bittorrent Client can be found here: https://github.com/litacho/bittorrent/

##Installation
This project is currently in progress so I haven't packaged it yet properly.
But you can install the necessary dependencies this way. Make a virtualenv and
within your project directory, run the following command:

`pip install -r requirements.txt`

##Running the program
All you need to do is pass in a valid torrent file where the tracker uses
the HTTP protocol. Still working on a UDP implementation!

`python reactor.py <your torrent file>.torrent`


To run with Gunicorn with multiple sessions:
gunicorn app:app  -k eventlet  -b 10.0.1.169 -w 3 (-w 3 will allow 3 processes)