import asyncio
from PIL import Image
import requests
import tempfile
from io import BytesIO
import binascii
import numpy as np
from scipy import cluster
import algorythm.spotipy_implementation as sp
import zmq

track_id = None

def collect_title_artist():
    global track_id
    sp.search_for_track(track_id)

def start_track_id_server():
    global track_id
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")

    while True:
        track_id = str(socket.recv())
        print("Received request: %s" % track_id)
        socket.send(b"")

def get_background_img(img_url):
    buffer = tempfile.SpooledTemporaryFile(max_size=1e9)
    r = requests.get(img_url, stream=True)
    if r.status_code == 200:
        downloaded = 0
        for chunk in r.iter_content(chunk_size=1024):
            downloaded += len(chunk)
            buffer.write(chunk)
        buffer.seek(0)
        i = Image.open(BytesIO(buffer.read()))
    buffer.close()
    return i

def generate_colors_from_img(img, num_colors):
    NUM_CLUSTERS = 5

    rgb_img = img.convert('RGB')
    ar = np.asarray(rgb_img)
    shape = ar.shape
    ar = ar.reshape(np.product(shape[:2]), shape[2]).astype(float)
    codes, dist = cluster.vq.kmeans(ar, NUM_CLUSTERS)
    vecs, dist = cluster.vq.vq(ar, codes)         # assign codes
    counts, bins = np.histogram(vecs, len(codes))    # count occurrences
    num_colors = len(counts) if len(counts) < num_colors else num_colors
    
    max_indeces = np.argpartition(counts, -1 * num_colors)[-1 * num_colors:]
    colors = [binascii.hexlify(bytearray(int(c) for c in codes[i])).decode('ascii') for i in max_indeces]
    return colors

def generate_colors(count=0):
    global track_id

    err = {'time_per_beat':1, 'colors':None, 'album_art':None}
    if track_id == None:
        return err
    try:
        track_img_url = sp.get_album_art(track_id)
        pil_img = get_background_img(track_img_url)
        features = sp.get_audio_features(track_id)
        tempo = float(features['track']['tempo'])
        time_per_beat = 60.0 / tempo # in sec
        time_sig = features['track']['time_signature']
        count = time_sig if count == 0 else count
        colors = generate_colors_from_img(pil_img, count)
        return {'time_per_beat':time_per_beat*time_sig, 'colors':colors, 'album_art':pil_img}
    except:
        return err
  
if __name__ == '__main__':
    print(generate_colors())
