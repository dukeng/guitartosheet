import matplotlib, numpy
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import wave
import struct
from scipy.io.wavfile import read as wavread

fig=plt.figure(figsize=(6,3))
fs = 44100 # sample rate

def getAutoCorellation(samples, size=2048):
  fft = numpy.fft.rfft(samples, size)
  # reverse fft of fft * its complex conjugate
  p1 = fft * numpy.conj(fft)
  p2 = p1 * numpy.conj(p1)
  return numpy.fft.irfft(p2 , size)

def getMaxPeak(samples):
  maxVal = 0
  maxI = 0
  start = False
  for i in range(1,len(samples)//2):
    if samples[i] < 0:
      start = True
    if not start:
      continue
    if samples[i] > samples[i-1] and samples[i] > samples[i+1]:
       if(samples[i] > maxVal):
         maxVal = samples[i]
         maxI = i
  return maxI

def readWavSamples(filename):
    [samplerate, vals] = wavread(filename)

    if isinstance(vals[0], numpy.ndarray):
      print("reading stereo file")
      samples = (vals[:,0]/2 + vals[:,1]/2 ) / 31
    else:
      print("reading mono file")
      samples = vals / 31
    return samples

def autoCorFreqEstimateOverTime(filename):
    samples = readWavSamples(filename)
    frameNum = 2048

    peaks = numpy.zeros(len(samples)//frameNum + 1)
    i = 0
    cur = 0

    while cur < len(samples):
      workingFrames = samples[cur:cur+2048]
      acor = getAutoCorellation(workingFrames)
      #return acor
      peaks[i] = getMaxPeak(acor)
      cur += frameNum
      i += 1
    newPeaks = 44100 / peaks
    for i in range(0,len(peaks)):
      if peaks[i] == 0:
        newPeaks[i] = 0
    return newPeaks

freqs = autoCorFreqEstimateOverTime('/Users/arrehnby/pdev/guitartosheet/guitar_tuning.wav')
#freqs = autoCorFreqEstimateOverTime('/Users/arrehnby/pdev/guitartosheet/test2.wav')

threshold = 3
deviation_threshold = 5
idx = 0
idx_jump = 1
while(idx < len(freqs)):
  sum = 0
  for j in range(0,threshold):
    if idx+j >= len(freqs):
      break
    freq = freqs[idx+j]
    sum += freq
  avg = sum / threshold
  deviation = 0
  for j in range(0,threshold):
    if idx+j >= len(freqs):
      break
    freq = freqs[idx+j]
    deviation += (avg - freq) * (avg - freq)
  std_deviation = numpy.sqrt(deviation / threshold)
  print("place: ", idx)
  if std_deviation < deviation_threshold:
    if idx+j >= len(freqs):
      break
    print("test1 freq: ", freqs[idx+j])
    for j in range(0,threshold):
      freqs[idx+j] = avg
    idx += threshold
  else:
    print("test2: ", std_deviation, " and " , deviation)
    for j in range(0,idx_jump):
      if idx+j >= len(freqs):
        break
      freqs[idx+j] = 0
    idx += idx_jump


plt.plot(freqs)

plt.savefig('freqs.png')
