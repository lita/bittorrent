import struct
import socket
import random
from urlparse import urlparse

import bencode
import requests

def make_connection_id_request():
    conn_id = struct.pack('>Q', 0x41727101980)
    action = struct.pack('>I', 0)
    trans_id = struct.pack('>I', random.randint(0, 100000))

    return (conn_id + action + trans_id, trans_id, action)

def make_announce_input(info_hash, conn_id, peer_id):
    action = struct.pack('>I', 1)
    trans_id = struct.pack('>I', random.randint(0, 100000))

    downloaded = struct.pack('>Q', 0)
    left = struct.pack('>Q', 0)
    uploaded = struct.pack('>Q', 0)

    event = struct.pack('>I', 0)
    ip = struct.pack('>I', 0)
    key = struct.pack('>I', 0)
    num_want = struct.pack('>i', -1)
    port = struct.pack('>h', 8000)

    return conn_id + action + trans_id + info_hash + peer_id + downloaded + left + uploaded + event + ip + key + num_want + port, trans_id, action

def send_msg(conn, sock, msg, trans_id, action, size):
    sock.sendto(msg, conn)
    try:
        response = sock.recv(2048)
    except socket.timeout as err:
        print err
        print "Connecting again..."
        return send_msg(conn, sock, msg, trans_id, action, size)
    if len(response) < size:
        print "Did not get full message. Connecting again..."
        return send_msg(conn, sock, msg, trans_id, action, size)

    if action != response[0:4] or trans_id != response[4:8]:
        print "Transaction or Action ID did not match. Connecting again..."
        return send_msg(conn, sock, msg, trans_id, action, size)

    return response

def scrape_udp(info_hash, announce, peer_id):
    parsed = urlparse(announce)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(8)
    conn = (socket.gethostbyname(parsed.hostname), parsed.port)
    msg, trans_id, action = make_connection_id_request()
    response = send_msg(conn, sock, msg, trans_id, action, 16)
    conn_id = response[8:]
    msg, trans_id, action = make_announce_input(info_hash, conn_id, peer_id)
    response = send_msg(conn, sock, msg, trans_id, action, 20)

    return response[20:]

def scrape_http(announce, info_hash, peer_id, length):
    params = {'info_hash': info_hash,
               'peer_id': peer_id,
               'left': length}

    response = requests.get(announce, params=params)


    if response.status_code > 400:
            errorMsg = ("Failed to connect to tracker.\n"
                        "Status Code: %s \n"
                        "Reason: %s") % (response.status_code, response.reason)
            raise RuntimeError(errorMsg)

    results =  bencode.bdecode(response.content)
    return results['peers']

    