import torrent_parser
import os
import hashlib

PIECE_LENGTH = 262144 # 2**18 = 256 KiB
PATH = './BitTorrent/Storage/'

def extract_info(filename,piece_length):
    name = PATH
    pieces = []
    length = os.stat(filename).st_size

    with open(filename,'rb') as f:
        while 1:
            data = f.read(piece_length)
            if not data:
                break
            piece = hashlib.sha1(data).hexdigest()
            pieces.append(piece)

    info = {
        'name': name,
        'piece_length': piece_length,
        'pieces' : pieces,
        'length' : length }

    metadata = {'info': info}
    return metadata

def build_torrent(filename, piece_length):
    metadata = extract_info(filename, piece_length)
    torrent_parser.create_torrent_file(f'{filename}.torrent',metadata)



# a = build_json('./Bella.MP3')
# a = build_json('./Alices-Adventures-in-Wonderland.pdf')
# a = build_json('./README.md')
# build_torrent('./README.md',PIECE_LENGTH )