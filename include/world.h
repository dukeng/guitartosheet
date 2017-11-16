#pragma once
#include <iostream>
#include <fstream>
#include <map>
#include <string>
#include <vector>
#include "display_music.h"
#include "alrm_lib.h"

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

struct World{
  Resources* resources;
  vector<Displayable> staves;
  vector<Displayable> symbols;
  vector<Note> notes;

  int startX = 150;
  int xIncSixteenth = 24;

  int a5Y = 110;
  int yStep = 12;

  // Additional spacing to add to notes in the second bar after the first
  int nextBarX = 40;

  int curX; // in pixels
  int curTime = 0; // in sixteenth notes

  int curY; // in pixels
  int curRow;

  // Spacing to next row of bars
  int fullDownSpacing;

  int notesRead = 0;

  // cur note #, location ect
  // distances to go for next note
  // when to change lines
  // bar information, tempo information, ect ect
  int barlineSpacing = -20;
};

void addRowToWorld(World* world){
  world->curRow++;
  world->curY = world->curRow*world->fullDownSpacing;
  world->curX = world->startX;

  int baseX = 50;
  int baseY = 50 + world->curY;

  Resources* resources = world->resources;

  Displayable stave = resources->displayables["stave"];
  stave.x = baseX;
  stave.y = baseY;
  world->staves.push_back(stave);
  stave.x += stave.w*stave.scaleFactor;
  world->staves.push_back(stave);

  // bass bars
  stave.x -= stave.w*stave.scaleFactor;
  stave.y += stave.h*stave.scaleFactor*2;
  world->staves.push_back(stave);
  stave.x += stave.w*stave.scaleFactor;
  world->staves.push_back(stave);

  // barline
  Displayable barline = resources->displayables["barline"];
  barline.x = baseX+world->barlineSpacing;
  barline.y = baseY;
  //world.staves.push_back(barline);

  barline.x += stave.w*stave.scaleFactor + 40;
  world->staves.push_back(barline);
  barline.x += stave.w*stave.scaleFactor - 40;
  world->staves.push_back(barline);

  Displayable treble= resources->displayables["trebleClef"];
  treble.x = baseX;
  treble.y = baseY - 10;

  Displayable bass = resources->displayables["bassClef"];
  bass.x = baseX;
  bass.y = baseY + stave.h*stave.scaleFactor*2 + 30;

  world->symbols.push_back(treble);
  world->symbols.push_back(bass);

}

World initWorld(Resources* resources){
  World world;
  world.resources = resources;

  world.curX = world.startX;
  world.curY = 0;
  world.curRow = -1;

  Displayable stave = resources->displayables["stave"];
  world.fullDownSpacing = stave.h*6;

  addRowToWorld(&world);

  return world;
}

void renderWorld(SDL_Renderer* renderer, World* world, SDL_Rect camera){
  for(int i = 0; i < world->staves.size(); i++){
    renderDisplayable(world->staves[i], renderer, camera);
  }
  for(int i = 0; i < world->symbols.size(); i++){
    renderDisplayable(world->symbols[i], renderer, camera);
  }
  for(int i = 0; i < world->notes.size(); i++){
    renderDisplayable(world->notes[i].dis, renderer, camera);
  }

}

void readNotesToWorld(string filePath, World* world){
  ifstream file(filePath);
  string ect;

  int tempo;
  int numNotes;
  file >> ect;
  file >> tempo;
  file >> ect;
  file >> numNotes;

  char note_locations[8] = "ABCDEFG";
  for(int i = 0; i < numNotes;i++){
    int note_time;
    string note_name;
    int note_type;
    file >> note_time;
    file >> note_name;
    file >> note_type;

    // cout << "test1. numNotes: " << numNotes << "" << "\n";
    if(i < world->notesRead){
      continue;
    }
    // cout << "test2: \n";
    world->notesRead++;

    char note_c = note_name[0];
    int noteNum = strchr(note_locations,note_c) - note_locations;
    int adj = note_name[1] - '0';

    int stepsFromCenter = (7*(5-adj)) - noteNum;
    int distFromCenter = world->a5Y + stepsFromCenter * world->yStep;

    // just calling everything a quarter note for now
    int noteLenMulti = 4;

    // todo: change to correct note for situation
    Note note = world->resources->notes["crotchetUp"];
    // this is currently assuming everything is a quarter note
    while(note_time >= 32*(world->curRow+1)){
      addRowToWorld(world);
      world->curX -= ((32*(world->curRow)) - world->curTime) * world->xIncSixteenth;
    }
    int timeDiff = (note_time-world->curTime);
    int note_time_local = note_time % 32;
    int cur_time_local = world->curTime % 32;
    if(note_time_local > 15 && cur_time_local <= 15){
      world->curX+=world->nextBarX;
    }
    cout << "diff: " << timeDiff << "\n";
    note.dis.x += world->curX + timeDiff*world->xIncSixteenth + noteLenMulti*(world->xIncSixteenth/2);
    note.dis.y += world->curY + distFromCenter;
    world->notes.push_back(note);
    cout << "x: " << note.dis.x << "\n";

    world->curTime = note_time;
    world->curX += timeDiff*world->xIncSixteenth;

  }
  file.close();
}
