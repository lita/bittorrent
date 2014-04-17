==========
Lita's Video Bittorrent Streamer
==========
This program is written on top of my Bittorrent Client. The bare bones of my 
Bittorrent Client can be found here: https://github.com/litacho/bittorrent/

##Installation
This project is currently in progress so I haven't packaged it yet properly.
But you can install the necessary dependencies this way. Make a virtualenv and
within your project directory, run the following command:

`pip install -r requirements.txt`

##Running the program
In order to run this program, you need to run it with Gunicorn. This program works with multiple clients, but it is pretty slow. So you should run it locally with one client.

`gunicorn app:app -t 10000000`

After launching, you can open your browser to http://localhost:8000/drop to load in a torrent file and watch movies.

In order to run with Gunicorn with multiple sessions, use the following command:

`gunicorn app:app  -k eventlet  -b [your computer's ip>]-w 3 (-w 3 will allow 3 processes)`

Go to http://[your computer's ip]:8000/drop to use the program.
