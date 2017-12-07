#pragma once
#include <map>
#include <fstream>
#include <string>
#include "alrm_lib.h"
#include "display_music.h"

using namespace std;

struct Resources{
  map<string, Displayable> displayables;
  map<string, Note> notes;
};

Resources loadResources(string imageLegendPath, SDL_Renderer* renderer){
  ifstream legendFile(imageLegendPath);
  Resources resources;

  string header;
  getline(legendFile, header);
  string name;
  while(getline(legendFile, name, ',')){
    trim(name);

    string type;
    getline(legendFile, type, ',');
    trim(type);

    string path;
    getline(legendFile, path, ',');
    trim(path);

    //cout << "path: " << path << "\n";

    string num;
    getline(legendFile, num, ',');
    float scaleFactor = ::atof(num.c_str());

    getline(legendFile, num, ',');
    float offset = ::atof(num.c_str());

    // extra
    string restOfTheLine;
    getline(legendFile, restOfTheLine);

    Displayable dis = loadDisplayable(path, renderer);
    dis.scaleFactor = scaleFactor;
    resources.displayables[name] = dis;

    if(type == "note"){
      cout << offset << "\n";
      cout << dis.h << "\n";
      int realOffset = (int)(offset * dis.h);
      cout << "foff1: " << realOffset;
      Note note = createNote(dis, 0, 0, realOffset);
      cout << "foff2: " << note.heightOffset;
      resources.notes[name] = note;
    }
  }
  legendFile.close();
  return resources;
}
