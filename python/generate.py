# tempo is defined as time between the two smallest notes in milliseconds
# each notes is defined as follows:
# [note_time, note_name, note_type]
# note time: time when note occurs in terms of the smallest note type
# note name: C5, D1, E4, ect
# note type: integer where 0 is the smallest note detected
def generate_note_file(tempo,notes):
    with open("note_output", "w") as fo:
        # write header
        fo.write("Tempo " + str(tempo) + " Notecount " + str(len(notes)) + "\n")
        # write notes
        for note in notes:
            note_timing = note[0]
            note_name = note[1]
            note_type = note[2]
            fo.write(str(note_timing) + " " + note_name + " " + str(note_type) + " ")

def main():
    # my code here
    notes = []
    notes.append([0,"C5",0])
    notes.append([1,"D5",0])
    notes.append([2,"E4",0])
    notes.append([3,"F7",0])
    #notes.append([5,"Eb4",0])
    #notes.append([6,"F#7",0])
    tempo = 50
    generate_note_file(tempo, notes)

if __name__ == "__main__":
    main()
