#pragma once
#include <iostream>
#include <fstream>
#include <map>
#include <string>
#include <vector>
#include "display_music.h"
#include "alrm_lib.h"
#include "resources.h"

using namespace std;

#define SCREEN_LOCATION_A4 110
#define OCTAVE_LENGTH 7

struct World{
  Resources* resources;
  vector<Displayable> staves;
  vector<Displayable> symbols;
  vector<Note> notes;

  int startX = 150;
  int xIncSixteenth = 24;

  int a4Y = SCREEN_LOCATION_A4;
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
    int adj;
    char acc = ' ';
    if(note_name[1] == '#' || note_name[1] == 'b'){
      acc = note_name[1];
      adj = note_name[2] - '0';
    }
    else{
      adj = note_name[1] - '0';
    }

    int stepsFromCenter = (7*(4-adj)) - noteNum;
    int distFromCenter = world->a4Y + stepsFromCenter * world->yStep;

    int noteLenMulti = 1 << note_type;

    Note note;
    if(note_type == 1)
      note = world->resources->notes["quaverUp"];
    if(note_type == 2)
      note = world->resources->notes["crotchetUp"];

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
    // cout << "diff: " << timeDiff << "\n";

    note.dis.x += world->curX + timeDiff*world->xIncSixteenth + noteLenMulti*(world->xIncSixteenth/2);
    note.dis.y += world->curY + distFromCenter;
    world->notes.push_back(note);

    if(acc != ' '){
      Displayable accidental;
      if(acc == '#'){
        accidental = world->resources->displayables["sharp"];
      }
      if(acc == 'b'){
        accidental = world->resources->displayables["flat"];
      }
      accidental.x = note.dis.x - 18;
      accidental.y = note.dis.y - note.heightOffset;
      world->symbols.push_back(accidental);
    }

    // cout << "x: " << note.dis.x << "\n";

    world->curTime = note_time;
    world->curX += timeDiff*world->xIncSixteenth;

  }
  file.close();
}
