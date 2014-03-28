==========
Lita's Bittorrent Client
==========

This program was a learning excerise about networking by writing
Bittorrent protocols from stratch. It is written in Python.

I used Kristen Widman's blog as a guide. Her posts were extremely helpful. 
I couldn't have gotten this far without her guide.

Part 1:
http://www.kristenwidman.com/blog/how-to-write-a-bittorrent-client-part-1

Part 2:
http://www.kristenwidman.com/blog/how-to-write-a-bittorrent-client-part-2

I also used the Bittorrent Unofficial Spec to format my packets.

https://wiki.theory.org/BitTorrentSpecification

Wireshark was also heavily used while debugging this software.

It is now asynchronous!!!

##Installation
This project is currently in progress so I haven't packaged it yet properly.
But you can install the necessary dependencies this way. Make a virtualenv and
within your project directory, run the following command:

`pip install -r requirements.txt`

##Running the program
All you need to do is pass in a valid torrent file where the tracker uses
the HTTP protocol. Still working on a UDP implementation!

`python reactor.py <your torrent file>.torrent`
