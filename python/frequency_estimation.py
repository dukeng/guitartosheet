import matplotlib, numpy
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import wave
import struct
import time
import queue
import subprocess
import pylab
import generate as note_output
from music21 import pitch
from scipy.io.wavfile import read as wavread

fig=plt.figure(figsize=(6,3))
fs = 44100 # sample rate
x = numpy.arange(fs)
frameNum = 2048

amp_threshold = 150
min_real_freq = 80
max_lookahead = 10
AMP_DELAY = 2


channels = [1]
downsample = 1
window = 200
mapping = [c - 1 for c in channels]  # Channel numbers start with 1
q = queue.Queue()

master_note_count = 0

count =  0
def audio_callback(indata, frames, Atime, status):
    """This is called (from a separate thread) for each audio block."""
    global count
    # print("count", count, "length", len(indata))
    count += 1
    # if status:
    #     print(status)
    #for item in np.ravel(indata):
    #  aFile.write("%s\n" % item)
    # aFile.write(np.ravel(indata))
    # Fancy indexing with mapping creates a (necessary!) copy:
    q.put(indata[::downsample, mapping])

from matplotlib.animation import FuncAnimation
import sounddevice as sd

length = int(window * fs / (1000 * downsample))
plotdata = numpy.zeros((length, len(channels)))
stream = sd.InputStream(
    device=5,channels=max(channels),
    samplerate=fs, callback=audio_callback)

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
  return maxI, maxVal

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
    # print("test2: ", len(samples))
    peaks = numpy.zeros(len(samples)//frameNum + 1)
    peakVals = numpy.zeros(len(samples)//frameNum + 1)
    i = 0
    cur = 0

    while cur < len(samples):
      workingFrames = samples[cur:cur+frameNum]
      acor = getAutoCorellation(workingFrames, frameNum)
      #return acor
      peaks[i],peakVals[i] = getMaxPeak(acor)
      # print("acor peak: ",peaks[i])
      cur += frameNum
      i += 1
    newPeaks = 44100 / peaks
    for i in range(0,len(peaks)):
      if peaks[i] == 0:
        newPeaks[i] = 0
    return newPeaks,peakVals

def amplitudeOverTime(samples):
    amplitudes = numpy.zeros(len(samples)//frameNum + 1)
    i = 0
    cur = 0

    while cur < len(samples):
      workingFrames = samples[cur:cur+frameNum]
      amplitudes[i] = peakRMS(workingFrames)
      # print("amp: ", amplitudes[i])
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
  # print("test: ", len(freqs))

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
    # print("place: ", idx)
    if std_deviation < deviation_threshold:
        if idx+j >= len(freqs):
            break
        # print("test1 freq: ", freqs[idx+j])
        for j in range(0,threshold):
            freqs[idx+j] = avg
        idx += threshold
    else:
        # print("test2: ", std_deviation, " and " , deviation)
        for j in range(0,idx_jump):
            if idx+j >= len(freqs):
                break
            freqs[idx+j] = 0
        idx += idx_jump
  return freqs

## Sudden amplitude peak == start of a note. Match that with the nearest detected frequency = note detected
def getNotes(freqs, amps, start_time):
    n_cnt = 0
    peak_amp = 0
    delay = AMP_DELAY
    i = delay
    notes = []
    while i < len(amps):
      if(amps[i] < peak_amp/5):
        # end note
        # print("note end: ", i)
        peak_amp = 0
        notes[-1].append(start_time+i-notes[-1][0])
      diff = amps[i] - amps[i-delay]
      if(diff > amp_threshold):
        n_cnt += 1
        if(peak_amp > 0):
          # end previous note if it's there
          notes[-1].append(start_time+i-notes[-1][0])
          peak_amp = 0
        #hit start of note
        #print("note start: ",i)
        j = min(i + 2,len(freqs)-1)
        while(freqs[j] < min_real_freq):
          if j >= len(amps)-1 or j >= max_lookahead:
              break;
          j += 1
        freq = freqs[j]
        #print("note frequency: ",freqs[j])
        if(freq > min_real_freq):
            notes.append([start_time+i, freqs[j]])
            peak_amp = amps[i]
        i += delay
      i += 1
    return notes

def checkThenExport(notes):
    global master_note_count
    if(len(notes) > master_note_count):
        master_note_count = len(notes)
        note_start_real = notes[0][0]
        for i in range(len(notes)):
            notes[i][0] -= note_start_real
        note_output.generate_note_file(50,notes)


def exportNotesToFile(notes):
    ## assume first note is quarter note
    quarter = notes[0][2]
    buckets = [max(quarter//4,1),max(quarter//2,1),quarter,quarter*2,quarter*4]
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
            # print("note len: ", note_len, ", bucket: ", buckets[j])
            diff = numpy.abs(buckets[j] - note_len)
            if diff < minDiff:
                note_len_adj = j
                minDiff = diff
        exportNotes.append([note_time_adj,p.name+str(p.octave),note_len_adj])
    checkThenExport(exportNotes)

allFreqs = numpy.zeros(0)
allAmps = numpy.zeros(0)
otherAmps = numpy.zeros(0)

frames_needed = fs * 3
freqs = numpy.zeros(0)
amps = numpy.zeros(0)
curtime = 0
frame_start = 0
allNotes = []

note_output.generate_note_file(50,[])
subprocess.Popen(["./guitartosheet"])

with stream:
    # keepGoing = True
    # while keepGoing:
    while len(allNotes) < 1000:
        detected_samples = []
        while(len(detected_samples) < frames_needed):
            window = q.get()
            #print("window: ", window)
            #print("window len: ", len(window))
            detected_samples.extend(window)
            #print("detected sample len: ", len(detected_samples))
            #print("q len: ", q.qsize())


        # fname = '/home/alrehn/dev/guitartosheet/pianoCMajor.wav'

        #audio_samples = readWavSamples(fname)
        # print("len samples: ", len(detected_samples))
        audio_samples = numpy.array([i[0] for i in detected_samples]);

        unsmoothed_freqs, acor_amps = autoCorFreqEstimateOverTime(audio_samples)
        # factor = 1000 / numpy.max(acor_amps)
        # acor_amps = acor_amps * factor
        # otherAmps = numpy.concatenate([otherAmps, acor_amps])
        # print("len unsmoothed_freqs: ", len(unsmoothed_freqs))

        newFreqs = smoothFrequencies(unsmoothed_freqs)
        # allFreqs = numpy.concatenate([allFreqs,newFreqs])#for plotting
        freqs = numpy.concatenate([freqs,newFreqs])

        newAmps = amplitudeOverTime(audio_samples)
        # allAmps = numpy.concatenate([allAmps,newAmps])#for plotting
        amps = numpy.concatenate([amps,newAmps])

        print("len freqs: ",len(freqs))
        print("len amps: ",len(amps))

        notes = getNotes(freqs, amps, curtime)
        print(notes)

        # cut off at the last detected note
        # if the note is finished, cut off at the end, if it isn't, cut off at the beginning
        if(len(notes) == 0):
            cutoff = 0
        else:
            last_note = notes[-1]
            if len(last_note) == 3:
                cutoff = last_note[0] - curtime + last_note[2] - AMP_DELAY
                allNotes.extend(notes)
            else:
                cutoff = last_note[0] - curtime - AMP_DELAY
                allNotes.extend(notes[:len(notes)-1])

        cutoff = max(0,cutoff)
        print("cutoff: ", cutoff)

        curtime = frame_start + cutoff
        frame_start += len(freqs)

        freqs = freqs[cutoff:]
        amps = amps[cutoff:]

        # plt.gcf().clear()
        # plt.plot(allFreqs)
        # plt.plot(allAmps)
        # plt.plot(otherAmps)
        # plt.savefig('freqs.png')

        if len(allNotes) > 0:
            exportNotesToFile(allNotes)

##TEMP
# notes = allNotes

# print("detected ", n_cnt, " notes")
# print(notes)

# frequency -> note, notes into bucket
# print(exportNotes)

