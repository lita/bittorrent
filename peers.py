
import hashlib

import bencode
import requests


class Peers(object):
    def __init__(self, trackerFile):
        self.peers = {}
        self.peer_id = '-lita38470993887523-'
        self.tracker = bencode.bdecode(open(trackerFile,'rb').read())
        self.infoHash = hashlib.sha1(bencode.bencode(self.tracker['info'])).digest()
        peersString = self.getPeers()
        self.peersString = peersString
        self.parseBinaryModelToString(peersString)


    def chunkToSixBytes(self, peerString):
        """
        Helper function to covert the string to 6 byte chunks.
        4 bytes for the IP address and 2 for the port.
        """
        for i in xrange(0, len(peerString), 6):
            chunk = peerString[i:i+6]
            if len(chunk) < 6:
                raise IndexError("Size of the chunk was not six bytes.")
            yield chunk

    def parseBinaryModelToString(self, peersString):
        """
        Converts the binary model, which is the string in
        hex, into an IP address and port number
        """
        for chunk in self.chunkToSixBytes(peersString):
            ip = []
            port = None
            for i in range(0, 4):

                ip.append(str(ord(chunk[i])))

            port = ord(chunk[4])*256+ord(chunk[5])
            self.peers['.'.join(ip)] = port

    def getPeers(self):
        # TODO: move the self.infoHash to init if we need it later.
        params = {'info_hash': self.infoHash,
                  'peer_id': self.peer_id,
                  'left': str(self.tracker['info']['piece length'])}
        response = requests.get(self.tracker['announce'], params=params)



        if response.status_code > 400:
            errorMsg = ("Failed to connect to tracker.\n"
                        "Status Code: %s \n"
                        "Reason: %s") % (response.status_code, response.reason)
            raise RuntimeError(errorMsg)

        result = bencode.bdecode(response.content)
        return result['peers']