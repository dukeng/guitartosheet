import matplotlib, numpy
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import wave
import struct
from scipy.io.wavfile import read as wavread

allSamples = np.array()



mapping = [c - 1 for c in args.channels]  # Channel numbers start with 1
# q = queue.Queue()

count =  0
def audio_callback(indata, frames, Atime, status):
    """This is called (from a separate thread) for each audio block."""
    global count
    print("count", count, "length", len(indata))
    count += 1
    if status:
        print(status, file=sys.stderr)
    for item in np.ravel(indata):
      aFile.write("%s\n" % item)
    time.sleep(2)
    # aFile.write(np.ravel(indata))
    # Fancy indexing with mapping creates a (necessary!) copy:
    # q.put(indata[::args.downsample, mapping])



try:
    from matplotlib.animation import FuncAnimation
    import matplotlib.pyplot as plt
    import numpy as np
    import sounddevice as sd

    if args.list_devices:
        print(sd.query_devices())
        parser.exit(0)
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, 'input')
        args.samplerate = device_info['default_samplerate']

    length = int(args.window * args.samplerate / (1000 * args.downsample))
    plotdata = np.zeros((length, len(args.channels)))

    # fig, ax = plt.subplots()
    # lines = ax.plot(plotdata)
    # if len(args.channels) > 1:
    #     ax.legend(['channel {}'.format(c) for c in args.channels],
    #               loc='lower left', ncol=len(args.channels))
    # ax.axis((0, len(plotdata), -1, 1))
    # ax.set_yticks([0])
    # ax.yaxis.grid(True)
    # ax.tick_params(bottom='off', top='off', labelbottom='off',
                   # right='off', left='off', labelleft='off')
    # fig.tight_layout(pad=0)

    stream = sd.InputStream(
        device=args.device, channels=max(args.channels),
        samplerate=args.samplerate, callback=audio_callback)

    # ani = FuncAnimation(fig, interval=args.interval, blit=True)
    # with stream:
        # pass

except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))





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

def autoCorFreqEstimateOverTime(samples):
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

def amplitudeOverTime(samples):
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

## Smooth frequencies detected, getting rid of outliers, only record frequencies if a group of detected frequencies are close to a certain average, then replace them all with that average
def smoothFrequencies(frequencies, threshold = 3, deviation_threshold = 10):
  idx = 0
  idx_jump = 1
  freqs = numpy.copy(frequencies)

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
  return freqs



fname = '/home/alrehn/dev/guitartosheet/pianoCMajor.wav'

audio_samples = readWavSamples(fname)

freqs = autoCorFreqEstimateOverTime(audio_samples)

plt.plot(freqs)

freqs = smoothFrequencies(freqs)

plt.plot(freqs)

amps = amplitudeOverTime(audio_samples)

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


