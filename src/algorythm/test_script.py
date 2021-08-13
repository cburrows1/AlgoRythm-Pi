import zmq

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")

while True:
    message = str(socket.recv())
    print("Received request: %s" % message)
    socket.send(b"")