#!/usr/bin/python3
import time
import pyaudio
import audioop
import systemd.daemon

from pixelflut import PixelClient
from colour import Color

CHUNK = 256
RATE = 4000 
maxValue = 2**16
bars=128
barHeight=8
scaleL=500
scaleR=500

maxDB = [0,0] #last peak value
maxDBT = [0,0] #last peak time
avrScale = [1]
DBALength = 100
startY = 17
endY = 32

pixelflut = PixelClient('10.208.42.159', 5004)
colors = list(Color("green").range_to(Color("red"), 129))
r = []
g = []
b = []
for color in colors:
    r.append(int(color.red * 255))
    g.append(int(color.green * 255))
    b.append(int(color.blue * 255))

p=pyaudio.PyAudio() # start the PyAudio class
stream=p.open(
        format=pyaudio.paInt16,
        channels=2, rate=RATE,
        input=True,
        frames_per_buffer=CHUNK) #uses default input device

def db_level(data, samplewidth=2, rms_mode=False):
        maxvalue = 2**(8*samplewidth-1)
        left_frames = audioop.tomono(data, samplewidth, 1, 0)
        right_frames = audioop.tomono(data, samplewidth, 0, 1)
        if rms_mode:
            peak_left = (audioop.rms(left_frames, samplewidth)+1)/maxvalue
            peak_right = (audioop.rms(right_frames, samplewidth)+1)/maxvalue
        else:
            peak_left = (audioop.max(left_frames, samplewidth)+1)/maxvalue
            peak_right = (audioop.max(right_frames, samplewidth)+1)/maxvalue
        return peak_left * 1000, peak_right * 1000

def valmap(value, istart, istop, ostart, ostop):
    return int(ostart + (ostop - ostart) * ((value - istart) / (istop - istart)))

def vuPixel(channel,value):
    startY = 16 + (barHeight * channel)
    if value > 127:
        value = 127
    if maxDB[channel] < value:
        maxDB[channel] = value
        maxDBT[channel] = time.time()
        avrScale.insert(0, value)
        if len(avrScale) > DBALength:
            avrScale.pop()
    for y in range(startY, startY+barHeight):
        for x in range(0,value):
            pixelflut.RGBPixel(x,y,r[x],g[x],b[x])
        for x in range(value,128):
            pixelflut.RGBPixel(x,y,0,0,0)
        pixelflut.RGBPixel(maxDB[channel],y,255,0,0)

if __name__ == '__main__':
    print('Starting up ...')
    systemd.daemon.notify('READY=1')
    while True:
        dbm = db_level(stream.read(CHUNK))
        scale = int(sum(avrScale) / len(avrScale))
        if scale < 10:
            scale = 500
        else:
            scale += 50 
        vuPixel(0,valmap(int(dbm[0]),0,scale,0,128))
        vuPixel(1,valmap(int(dbm[1]),0,scale,0,128))
        pixelflut.flush()
        now = time.time()
        if (now - maxDBT[0]) > 1.5:
            maxDB[0] = 1
        if (now - maxDBT[1]) > 1.5:
            maxDB[1] = 1

    stream.stop_stream()
    stream.close()
    p.terminate()
