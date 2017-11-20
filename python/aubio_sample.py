#! /usr/bin/env python

import sys
from aubio import source, pitch

if len(sys.argv) < 2:
    print("Usage: %s <filename> [samplerate]" % sys.argv[0])
    sys.exit(1)

filename = sys.argv[1]

downsample = 1
samplerate = 44100 // downsample
if len( sys.argv ) > 2: samplerate = int(sys.argv[2])

win_s = 4096 // downsample # fft size
hop_s = 512  // downsample # hop size

s = source(filename, samplerate, hop_s)
samplerate = s.samplerate

tolerance = 0.6

pitch_o = pitch("yin", win_s, hop_s, samplerate)
pitch_o.set_unit("midi")
pitch_o.set_tolerance(tolerance)

pitches = []
confidences = []


saved_pitch = []

# total number of frames read
total_frames = 0
while True:
    samples, read = s()
    pitch = pitch_o(samples)[0]
    #pitch = int(round(pitch))
    confidence = pitch_o.get_confidence()
    #if confidence < 0.8: pitch = 0.
    print("%f %f %f" % (total_frames / float(samplerate), pitch, confidence))
    saved_pitch.append([total_frames / float(samplerate)])
    pitches += [pitch]
    confidences += [confidence]
    total_frames += read
    if read < hop_s: break

if 0: sys.exit(0)


FILE_LENGTH = (total_frames / float(samplerate))

#print pitches
import os.path
from numpy import array, ma
import matplotlib.pyplot as plt
# from demo_waveform_plot import get_waveform_plot, set_xlabels_sample2time

# import sys
# from aubio import source
from numpy import zeros, hstack, median




def get_waveform_plot(filename, samplerate = 0, block_size = 4096, ax = None, downsample = 2**4):
    import matplotlib.pyplot as plt
    if not ax:
        fig = plt.figure()
        ax = fig.add_subplot(111)
    hop_s = block_size

    allsamples_max = zeros(0,)
    downsample = downsample  # to plot n samples / hop_s

    a = source(filename, samplerate, hop_s)            # source file
    if samplerate == 0: samplerate = a.samplerate

    total_frames = 0
    while True:
        samples, read = a()
        # keep some data to plot it later
        new_maxes = (abs(samples.reshape(hop_s//downsample, downsample))).max(axis=0)
        allsamples_max = hstack([allsamples_max, new_maxes])
        total_frames += read
        if read < hop_s: break
    allsamples_max = (allsamples_max > 0) * allsamples_max
    allsamples_max_times = [ ( float (t) / downsample ) * hop_s for t in range(len(allsamples_max)) ]

    ax.plot(allsamples_max_times,  allsamples_max, '-b')
    ax.plot(allsamples_max_times, -allsamples_max, '-b')
    ax.axis(xmin = allsamples_max_times[0], xmax = allsamples_max_times[-1])

    set_xlabels_sample2time(ax, allsamples_max_times[-1], samplerate)
    return ax, allsamples_max

def set_xlabels_sample2time(ax, latest_sample, samplerate):
    ax.axis(xmin = 0, xmax = latest_sample)
    if latest_sample / float(samplerate) > 60:
        ax.set_xlabel('time (mm:ss)')
        ax.set_xticklabels([ "%02d:%02d" % (t/float(samplerate)/60, (t/float(samplerate))%60) for t in ax.get_xticks()[:-1]], rotation = 50)
    else:
        ax.set_xlabel('time (ss.mm)')
        ax.set_xticklabels([ "%02d.%02d" % (t/float(samplerate), 100*((t/float(samplerate))%1) ) for t in ax.get_xticks()[:-1]], rotation = 50)




skip = 1

pitches = array(pitches[skip:])
confidences = array(confidences[skip:])
times = [t * hop_s for t in range(len(pitches))]

fig = plt.figure()

ax1 = fig.add_subplot(311)
ax1, allsamples_max = get_waveform_plot(filename, samplerate = samplerate, block_size = hop_s, ax = ax1)
plt.setp(ax1.get_xticklabels(), visible = False)
ax1.set_xlabel('')

def array_from_text_file(filename, dtype = 'float'):
    filename = os.path.join(os.path.dirname(__file__), filename)
    return array([line.split() for line in open(filename).readlines()],
        dtype = dtype)

ax2 = fig.add_subplot(312, sharex = ax1)
ground_truth = os.path.splitext(filename)[0] + '.f0.Corrected'
if os.path.isfile(ground_truth):
    ground_truth = array_from_text_file(ground_truth)
    true_freqs = ground_truth[:,2]
    true_freqs = ma.masked_where(true_freqs < 2, true_freqs)
    true_times = float(samplerate) * ground_truth[:,0]
    ax2.plot(true_times, true_freqs, 'r')
    ax2.axis( ymin = 0.9 * true_freqs.min(), ymax = 1.1 * true_freqs.max() )
# plot raw pitches
ax2.plot(times, pitches, '.g')
# plot cleaned up pitches
cleaned_pitches = pitches
print("uncleaned", len(cleaned_pitches))    
cleaned_pitches = ma.masked_where(cleaned_pitches < 0, cleaned_pitches)
cleaned_pitches = ma.masked_where(cleaned_pitches > 120, cleaned_pitches)
cleaned_pitches = ma.masked_where(confidences < tolerance, cleaned_pitches)

total_frames = 0
idx = 0
assert len(cleaned_pitches) == len(pitches)
for aPitch in cleaned_pitches:
    if aPitch != '--':
        saved_pitch[idx].append(int(round(aPitch)))
        idx += 1
print(len(cleaned_pitches))
diff = 0
start = 0
notes = []

import math

f = open('result.txt','w')

operate_pitches = [int(round(i)) for i in cleaned_pitches.compressed().tolist()]
# operate_pitches = pitches
print(len(operate_pitches))
bucket = dict()
for index in range(1, len(operate_pitches)):
    # print(abs(operate_pitches[index] - operate_pitches[index - 1]))
    # f.write(str(operate_pitches[index]) + '\n')
    if str(operate_pitches[index]) not in bucket:
        bucket[str(operate_pitches[index])] = 0
    bucket[str(operate_pitches[index])] += 1
    if abs(operate_pitches[index] - operate_pitches[index - 1]) >= 0.9: # new note
        # print("got here")
        if start == 0:
            start = index
        else:
            # print("median", median(operate_pitches[start:index + 1]) , "mean", sum(operate_pitches[start:index + 1]) // (index - start))
            notes.append( (median(operate_pitches[start:index + 1]), start, index))
            start = 0
    else:
        pass

if start != 0:
    notes.append((median(operate_pitches[start:len(operate_pitches) + 1]), start, len(operate_pitches) + 1))
# print(notes)
# print(len(notes))
print(bucket)
defined_note_threshold = 20
filtered_bucket = []
for midi, count in bucket.items():
    if int(midi) != 0 and count > defined_note_threshold:
        filtered_bucket.append(int(midi))

print("filtered_bucket", filtered_bucket)
print("length all_sample_max", len(allsamples_max))

general_notes_detected = []

current_note = None
start_time = 0
current_instance = 0
misNote_threshold = 5
note_threshold = 15
tolerance_instance = misNote_threshold
for entry in saved_pitch:
    if len(entry) < 2:
        continue
    midi_note = entry[1]
    if midi_note != 0 and  midi_note in filtered_bucket:
        if current_note == None:
            current_note = midi_note
            print(current_note)
            start_time = entry[0] # the time the note starts
        if midi_note == current_note:
            current_instance += 1
        elif midi_note != current_note:
            if tolerance_instance > 0: # tolerate notes that are outliers
                tolerance_instance -= 1
            else:
                if current_note != None:
                    print("current_instance", current_instance)
                    if current_instance > note_threshold:
                        general_notes_detected.append((current_note, start_time, entry[0], entry[0] - start_time))
                    tolerance_instance = misNote_threshold
                    current_note = None
                    current_instance = 0

if current_note != None:
    print("current_instance", current_instance)
    if current_instance > note_threshold:
        general_notes_detected.append((current_note, start_time, entry[0], entry[0] - start_time))
    current_note = None
    current_instance = 0

print("midiNote", ",start_time", ",end_time", ",duration")
for tuple in general_notes_detected:
    print(tuple)
# print(general_notes_detected)
print("length", len(general_notes_detected))

#length_all_sample_max = len(allsamples_max)
length_confidence = len(confidences)
note_threshold2 = 50
low_threshold = 0.05
note_time = 0
detected_notes = []

idx = 0
while idx < length_confidence:
    if confidences[idx] < low_threshold and note_time > 0 and len(detected_notes[-1]) == 2:
        next_note_time = FILE_LENGTH * (idx / length_confidence)
        detected_notes[-1].append(next_note_time - note_time)
    if confidences[idx] > 0.75 and confidences[idx - note_threshold2] < 0.75:
        next_note_time = FILE_LENGTH * (idx / length_confidence)
        if(note_time > 0) and len(detected_notes[-1]) == 2:
            detected_notes[-1].append(next_note_time - note_time)
        note_time = next_note_time
        for note in general_notes_detected:
            if note_time > note[1] and note_time < note[2]:
                detected_notes.append([note[0], note_time])
                break
        idx += note_threshold2
    idx += 1

if len(detected_notes[-1]) == 2:
        next_note_time = FILE_LENGTH * (idx / length_confidence)
        detected_notes[-1].append(next_note_time - note_time)
print(detected_notes)
print(len(detected_notes))


f.close()


conversion_file = open('midi_note_conversion.txt','r')

conversion_dictionary = dict()
for line in conversion_file:
    line = line.strip().split("\t")
    if len(line) == 3:
        conversion_dictionary[int(line[0])] = line[1]

print(conversion_dictionary)

for detected_note in detected_notes:
    detected_note[0] = conversion_dictionary[detected_note[0]]


print(detected_notes)

import generate

notes = []

cur = 0
for detected_note in detected_notes:
    note = [cur, detected_note[0], 2]
    notes.append(note)
    cur += 4

generate.generate_note_file(50, notes)

ax2.plot(times, cleaned_pitches, 'b')
ax2.axis( ymin = 0.9 * cleaned_pitches.min(), ymax = 1.1 * cleaned_pitches.max() )
ax2.axis( ymin = 20, ymax = 90 )
plt.setp(ax2.get_xticklabels(), visible = False)
ax2.set_ylabel('f0 (midi)')

# plot confidence
ax3 = fig.add_subplot(313, sharex = ax1)
# plot the confidence
ax3.plot(times, confidences)
# draw a line at tolerance
ax3.plot(times, [tolerance]*len(confidences))
ax3.axis( xmin = times[0], xmax = times[-1])
ax3.set_ylabel('condidence')
set_xlabels_sample2time(ax3, times[-1], samplerate)

plt.show()

plt.savefig(os.path.basename(filename) + '.png')
