import zmq
import os

if(os.environ['PLAYER_EVENT'] == 'playing'):
    msg = str(os.environ['TRACK_ID'])
    context = zmq.Context()

    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5555")

    socket.send(bytes(msg,'utf-8'))
    message = socket.recv()