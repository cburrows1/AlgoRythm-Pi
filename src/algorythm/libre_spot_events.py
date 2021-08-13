#!/usr/bin/env python3
from multiprocessing import Process,Pipe
import os

def f(child_conn):
    if(os.environ['PLAYER_EVENT'] == 'playing'):
        msg = str(os.environ['TRACK_ID'])
        child_conn.send(msg)
        child_conn.close()