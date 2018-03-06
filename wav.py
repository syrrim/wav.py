import sys
from time import *
from math import *
from itertools import *
from functools import *
from operator import *

def frange(start, stop, step=1):
    for i in range(int((stop-start)/step)):
        yield start + i*step

def mrange(start, stop, number):
    fac = stop/start
    for i in range(int(number)):
        yield start * fac ** (i/number)
        
def lit_end(l, num):
    for i in range(l):
        d, m = divmod(num, 256)
        yield m
        num = d
    if num:
        raise Exception("num not fully written")

def big_end(l, num):
    return reversed(list(lit_end(l, num)))

def wbytes(f, bs):
    f.write(bytes(bs))

class WAV:
    def __init__(self, chn=2, rate=44100, sample=2):
        self.chn = chn 
        self.rate = rate
        self.sample = sample
        self.size = 0

    def wave(self, freq_it, form):
        for i in accumulate(map(lambda freq: freq/self.rate, freq_it)):
            yield form((i*2%2)-1)

    def staticwave(self, freq, form):
        return self.wave(repeat(freq), form)

    def fade(self, secs, it, pattern):
        return starmap(lambda i, x: pattern(i) * x, zip(frange(1, 0, -1/(secs * self.rate)), it))

    def length(self, secs, it):
        return self.fade(secs, it, lambda i:1)

    def write_header(self, f):
        f.write(b"RIFF")
        wbytes(f, lit_end(4, self.size+44))
        f.write(b"WAVE")
        f.write(b"fmt ")
        wbytes(f, lit_end(4, 16))
        wbytes(f, lit_end(2, 1))
        wbytes(f, lit_end(2, self.chn))
        wbytes(f, lit_end(4, self.rate))
        wbytes(f, lit_end(4, self.chn * self.rate * self.sample))
        wbytes(f, lit_end(2, self.sample * self.chn))
        wbytes(f, lit_end(2, self.sample * 8))
        f.write(b"data")
        wbytes(f, lit_end(4, self.size))
    
    def write_data(self, f, it):
        for i, n in enumerate(it):
            if self.sample < 2:
                wbytes(f, lit_end(self.sample, int((n+1)/2 * (256**self.sample - 1))))
            else:
                a = (n/2+1)%1
                wbytes(f, lit_end(self.sample, int((a) * (256**self.sample - 1))))
            self.size += self.sample

    def write_channels(self, f, *it):
        if len(it) != self.chn:
            pass#raise Exception(f"numbers of its ({len(it)}) doesn't match number of channels ({self.chn})")

        return self.write_data(f, chain(*zip(*it)))

def combine(*pairs):
    _, weights = zip(*pairs)
    weight = sum(weights)
    return map(sum, zip(*starmap(lambda it, w: starmap(mul, zip(it, repeat(w/weight))), pairs)))

#waveforms:
SAWTOOTH = lambda i:i
SQUARE = lambda i: -1 if i < 0 else 1
TRIANGLE = lambda i: abs(i)*2-1
SIN = lambda i: sin(i * pi)

#frequencies:
OCT = 2
HS = OCT**(1/12)
WS = HS**2
MAJOR = [WS, WS, HS, WS, WS, WS, HS]
MINOR = MAJOR[5:] + MAJOR[:5]
MINOR = [WS, HS, WS, WS, HS, WS, WS]

m2, M2, m3, M3, P4, TT, P5, m6, M6, m7, M7, OCT = accumulate([HS]*12, mul)
#m2,    M2,  m3,    M3,  P4,  TT,     P5,  m6,    M6,    m7,    M7,   OCT = \
#[18/17, 9/8, 19/16, 5/4, 4/3, 17/12, 3/2, 27/17, 32/19, 41/23, 17/9, 2]

ACCMAJ = [1, M2, M3, P4, P5, M6, M7, OCT]
ACCMIN = [1, m2, m3, P4, P5, m6, m7, OCT]

A4 = 440
C4 = A4 * HS**3 / OCT
C4, D4, E4, F4, G4, A4, B4, C5 = accumulate([C4, *MAJOR], mul)
C4, D4, E4, F4, G4, A4, B4, C5 = map(partial(mul, C4), ACCMAJ)

#fades:
def interpolate(i, li):
    p = i * (len(li)-2)
    b = int(p)
    t = b + 1
    d = p - b
    return li[b] + d * (li[t] - li[b])

LINE = lambda i: i
TAIL = lambda i: i**2
QUICK = lambda i: i**.5
#REVERB = lambda i: i/1.1 + sin(i*pi*200)/20 * i

if __name__ == "__main__":
    fn = "sound.wav"

    with open(fn, "wb") as f:
        wav = WAV(chn=2, sample=2)
        wav.write_header(f)

        #wav.write_data(f, map(lambda i: i * .4, wav.wave(mrange(A4, A4*OCT**3, wav.rate * 10), SIN)))

        #wav.write_data(f, chain(*map(lambda freq: wav.length(1, wav.staticwave(freq, SIN)), accumulate([C4, *MAJOR], mul))))

        def note(n, l=1): 
            wav.write_data(f, map(lambda i:i*.3, wav.fade(l, wav.staticwave(n, SIN), QUICK)))
        E3, F3, G3, A3, B3,   = E4/OCT,F4/OCT,G4/OCT,A4/OCT,B4/OCT
        if sys.argv[1:]:
            for arg in sys.argv[1:]:
                note(eval(arg))
        else:
            for n in [E4,E4,E4,D4,C4,D4,C4,C4,D4,E4,G4,E4,D4,C4,A3,A3,A3,E4,D4,C4,B3,B3,C4,A3,A3,E4,E4,E4,D4]:
                note(n)

        #wav.write_data(f, map(lambda i:i*.4, wav.fade(7, 
        #    combine(
        #        (wav.staticwave(C4*P5, SIN), 3),
        #        (wav.staticwave(C4*M3, SIN), 4),
        #        (wav.staticwave(C4*M3/OCT, SIN), .7),
        #        (wav.staticwave(C4, SIN), 5),
        #        (wav.staticwave(C4/OCT, SIN), 5),
        #        (wav.staticwave(C4/OCT/OCT, SIN), 5),
        #    ), 
        #QUICK)))
        wav.size -= 1
        f.seek(0)
        wav.write_header(f)

