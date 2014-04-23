==========
Lita's Bittorrent Client
==========

This program is a command line tool that downloads a file from the Bittorrent network given a torrent file. It is able to connect to multiple peers, and use trackers using HTTP and UDP. It is written in Python.

This program was a learning exercise about networking and asynchronous I/O. Most of the program is written from scratch. I only use the bencode library to parse the torrent file, requests to send GET requests to the tracker (although I wrote a library to communicate with the tracker through UDP), and bitstring to have a robust bit array data structure.

###Things I've Learned from this Project:
* The Bittorrent Protocol 
* Working with UDP packets
* How to use Wireshark for debugging
* Write asynchronous programs
* Network programming in Python (sending packets, dealing with network errors, managing multiple IO connections)
* HTTP Protocals with video streaming. The power of HTML5 <video> tag!
* Flask API
* Concurrancy in Python! Use multiprocessing rather than threading unless you are doing IO!

###TODO List:
* Handle uploading a file.
* Optimize which piece to download by finding the rarest piece.
* Reconnect to more peers when they drop.

I used Kristen Widman's blog as a guide. Her posts were extremely helpful. 
I couldn't have gotten this far without her guide.

Part 1:
http://www.kristenwidman.com/blog/how-to-write-a-bittorrent-client-part-1

Part 2:
http://www.kristenwidman.com/blog/how-to-write-a-bittorrent-client-part-2

I also used the Bittorrent Unofficial Spec to format my packets.

https://wiki.theory.org/BitTorrentSpecification

##Installation
This project is currently in progress so I haven't packaged it yet properly.
But you can install the necessary dependencies by using pip. Just run the following command:

`pip install -r requirements.txt`

##Running the program
All you need to do is pass in a valid torrent file:

`python run.py <your torrent file>.torrent`

