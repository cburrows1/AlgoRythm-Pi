import pyaudio
import numpy as np
from scipy.fft import rfft, rfftfreq
import time

FORMAT = pyaudio.paFloat32 # use float to restrict values between (0, 1)
CHANNELS = 1 # use 1 channel for now, can try to visualize stereo later
RATE = 44100 # Audio sample rate, shouldn't need to be adjusted
chunk = 8192 # lower number is less latency, higher number improves performance

KEEP_FRAMES = 10 #number of frames to keep in the list (mostly just need most recent frame)

recent_frames = []
last_freqs = None
last_levels = None
stream = None

# p = pyaudio.PyAudio()

# def callback(in_data, frame_count, time_info, status):
#     global recent_frames, last_freqs, last_levels
    
#     numpydata = np.frombuffer(in_data, dtype=np.float32)
    
#     yf = np.abs(rfft(numpydata))
#     xf = rfftfreq(chunk, 1 / RATE)

#     #normalization of fft values - other methods could be investigated
#     yl = 1.0 / (chunk / 3) * yf
    
#     bins = list(zip(xf, yl))
#     recent_frames.append(bins)
#     recent_frames = recent_frames[-1 * KEEP_FRAMES:]
    
#     last_freqs = xf[:(chunk+1)//3]
#     last_levels = yl[:(chunk+1)//3]
    
#     return (yl,pyaudio.paContinue)

# def start_stream(settings):
#     global stream,p,chunk
#     chunk = settings.b_count * 3 - 1


#     stream = p.open(format = FORMAT,
#                     channels = CHANNELS,
#                     rate = RATE,
#                     input = True,
#                     device='hw:1,1',
#                     frames_per_buffer = chunk,
#                     stream_callback=callback)

#     stream.start_stream()

# def stop_stream():
#     stream.stop_stream()
#     stream.close()
#     p.terminate()

# def restart_stream(settings):
#     # clear and remake stream to update chunk
#     global recent_frames, last_freqs, last_levels
#     stream.stop_stream()
#     stream.close()

#     recent_frames = []
#     last_freqs = None
#     last_levels = None

#     start_stream(settings)

# if __name__ == '__main__':
#     start_stream()
#     while stream.is_active():
#         if len(recent_frames) > 0:
#             print(recent_frames[-1][:5])

#         time.sleep(0.1)
#     stop_stream()


from collections import deque
import struct
import sys
import threading
import alsaaudio

class Sampler(threading.Thread):
    def __init__(self, NB_SAMPLE):
        threading.Thread.__init__(self)
        self.daemon = True
        self.inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE,device='hw:1,1',channels=1,rate=NB_SAMPLE,periodsize=8192,format=alsaaudio.PCM_FORMAT_S16_LE)
        self.inp.setchannels(1)
        # sample FIFO
        self._s_lock = threading.Lock()
        self._s_fifo = deque([0] * NB_SAMPLE, maxlen=NB_SAMPLE)

    def get_levels(self):
        global recent_frames,last_freqs,last_levels
        yf = np.abs(rfft(self.get_sample()))
        xf = rfftfreq(chunk, 1 / RATE)

        #normalization of fft values - other methods could be investigated
        yl = 1.0 / (chunk / 3) * yf
        
        bins = list(zip(xf, yl))
        recent_frames.append(bins)
        recent_frames = recent_frames[-1 * KEEP_FRAMES:]
        
        last_freqs = xf[:(chunk+1)//3]
        last_levels = yl[:(chunk+1)//3]

    def get_sample(self):
        with self._s_lock:
            return list(self._s_fifo)

    def run(self):
        while True:
            # read data from device
            l, data = self.inp.read()
            if l > 0:
                # extract and format sample (normalize sample to 1.0/-1.0 float)
                raw_smp_l = struct.unpack('h' * (l*2), data)
                smp_l = (float(raw_smp / 32767) for raw_smp in raw_smp_l)
                with self._s_lock:
                    self._s_fifo.extend(smp_l)
            else:
                print('sampler error occur (l=%s and len data=%s)' % (l, len(data)), file=sys.stderr)
