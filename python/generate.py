import subprocess

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
            print(note_timing)
            print(note_name)
            print(note_type)
            fo.write(str(note_timing) + " " + note_name + " " + str(note_type) + " ")

def main():
    # my code here
    notes = []
    notes.append([0,"C5",2])
    #notes.append([4,"D5",0])
    # notes.append([8,"E4",0])
    # notes.append([12,"F5",0])
    # notes.append([16,"C5",0])
    # notes.append([20,"D5",0])
    # notes.append([24,"E4",0])
    # notes.append([28,"F5",0])
    # notes.append([32,"F5",0])
    # # notes.append([36,"F5",0])
    # notes.append([50,"E5",0])
    # notes.append([54,"E5",0])
    # notes.append([58,"E5",0])
    tempo = 50
    generate_note_file(tempo, notes)

    subprocess.Popen(["./guitartosheet"])

    cur = 4;

    while True:
        note_name = raw_input("\nEnter a note: ")
        notes.append([cur,note_name,2])
        generate_note_file(tempo, notes)
        cur += 4;



if __name__ == "__main__":
    main()
