import matplotlib, numpy
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import wave
import struct
from scipy.io.wavfile import read as wavread

fig=plt.figure(figsize=(6,3))
fs = 44100 # sample rate
x = numpy.arange(fs)
frameNum = 2048

def sinWave(frequency, amplitude, phase=0, duration = 1.0):
    sNum = fs * duration
    return amplitude * numpy.sin(2*numpy.pi*frequency*x/sNum + phase)

def innerProdAmp(freq, signal, duration=1.0, phase=0):
    unitSin = sinWave(freq, 1.0, phase, duration)
    return numpy.dot(signal,unitSin) * 2 / len(unitSin)

def peakRMS(samples):
    return numpy.sqrt(numpy.mean(numpy.square(samples)))

def getAutoCorellation(samples,size):
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

    peaks = numpy.zeros(len(samples)//frameNum + 1)
    i = 0
    cur = 0

    while cur < len(samples):
      workingFrames = samples[cur:cur+frameNum]
      acor = getAutoCorellation(workingFrames, frameNum)
      #return acor
      peaks[i] = getMaxPeak(acor)
      print("acor peak: ",peaks[i])
      cur += frameNum
      i += 1
    newPeaks = 44100 / peaks
    for i in range(0,len(peaks)):
      if peaks[i] == 0:
        newPeaks[i] = 0
    return newPeaks

def amplitudeOverTime(filename):
    samples = readWavSamples(filename)

    amplitudes = numpy.zeros(len(samples)//frameNum + 1)
    i = 0
    cur = 0

    while cur < len(samples):
      workingFrames = samples[cur:cur+frameNum]
      amplitudes[i] = peakRMS(workingFrames)
      print("amp: ", amplitudes[i])
      cur += frameNum
      i += 1

    factor = 1000 / numpy.max(amplitudes)
    amplitudes = amplitudes * factor

    return amplitudes

fname = '/home/alrehn/dev/guitartosheet/pianoCMajor.wav'

#freqs = autoCorFreqEstimateOverTime('/Users/arrehnby/pdev/guitartosheet/guitar_tuning.wav')
#freqs = autoCorFreqEstimateOverTime('/Users/arrehnby/pdev/guitartosheet/test2.wav')
freqs = autoCorFreqEstimateOverTime(fname)

plt.plot(freqs)

## Smooth frequencies detected, getting rid of outliers, only record frequencies if a group of detected frequencies are close to a certain average, then replace them all with that average
threshold = 3
deviation_threshold = 10
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

amps = amplitudeOverTime(fname)

plt.plot(amps)

plt.savefig('freqs.png')

print(len(freqs))
print(len(amps))

## Sudden amplitude peak == start of a note. Match that with the nearest detected frequency = note detected
n_cnt = 0
amp_threshold = 30
min_real_freq = 80
peak_amp = 0
delay = 3
i = delay
notes = []
while i < len(amps):
  if(amps[i] < peak_amp/25):
    # end note
    print("note end: ", i)
    peak_amp = 0
    notes[-1].append(i-notes[-1][0])
  diff = amps[i] - amps[i-delay]
  if(diff > amp_threshold):
    n_cnt += 1
    if(peak_amp > 0):
      # end previous note if it's there
      notes[-1].append(i-notes[-1][0])
      peak_amp = 0
    peak_amp = amps[i]
    #hit start of note
    #print("note start: ",i)
    j = min(i + 8,len(amps)-1)
    while(freqs[j] < min_real_freq):
      if j >= len(amps)-1:
          break;
      j += 1
    freq = freqs[j]
    #print("note frequency: ",freqs[j])
    i += delay
    notes.append([i, freqs[j]])
  i += 1

print("detected ", n_cnt, " notes")
print(notes)

## assume first note is quarter note
quarter = notes[0][2]
buckets = [quarter//4,quarter//2,quarter,quarter**2,quarter**4]
#print("b: ", buckets[0], buckets[1], buckets[2])

from music21 import pitch

# frequency -> note, notes into buckets
exportNotes = []
for i in range(len(notes)):
  if notes[i][1] < min_real_freq:
      continue;
  p = pitch.Pitch()
  p.frequency = notes[i][1]
  note_time_adj = notes[i][0] // buckets[0]
  note_len = notes[i][2]
  note_len_adj = 0
  minDiff = 10000
  for j in range(len(buckets)):
    diff = numpy.abs(buckets[j] - note_len)
    if diff < minDiff:
      note_len_adj = j
      minDiff = diff
  exportNotes.append([note_time_adj,p.name+str(p.octave),note_len_adj])

print(exportNotes)

plt.savefig('freqs.png')
