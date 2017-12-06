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

  bool freeCamera = false;

  int startX = 150;
  int xIncSixteenth = 24;

  int a4Y = SCREEN_LOCATION_A4;
  int yStep = 12;

  // Additional spacing to add to notes in the second bar after the first
  int nextBarX = 40;

  int curX; // in pixels
  int curTime; // in sixteenth notes

  int curY; // in pixels
  int curRow;

  int noteTypeAdj = 0;

  // Spacing to next row of bars
  int fullDownSpacing;

  int notesRead;

  int timeSig = 4;

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
  // stave.x -= stave.w*stave.scaleFactor;
  // stave.y += stave.h*stave.scaleFactor*2;
  // world->staves.push_back(stave);
  // stave.x += stave.w*stave.scaleFactor;
  // world->staves.push_back(stave);

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

  Displayable timeSigImg;
  if(world->timeSig == 4){
    timeSigImg = resources->displayables["4-4"];
  }
  else if(world->timeSig = 3){
    timeSigImg = resources->displayables["3-4"];
  }
  else{
    cout << "ERROR: bad time signature: " << world->timeSig << "\n";
    timeSigImg = resources->displayables["4-4"];
  }
  timeSigImg.x = baseX + 50;
  timeSigImg.y = baseY;


  // Displayable bass = resources->displayables["bassClef"];
  // bass.x = baseX;
  // bass.y = baseY + stave.h*stave.scaleFactor*2 + 30;

  world->symbols.push_back(treble);
  world->symbols.push_back(timeSigImg);
  // world->symbols.push_back(bass);

}

void resetWorld(World* world){

  world->curX = world->startX;
  world->curY = 0;
  world->curRow = -1;

  world->notes.clear();
  world->staves.clear();
  world->symbols.clear();

  world->curTime = 0;
  world->notesRead = 0;

  Displayable stave = world->resources->displayables["stave"];
  // world->fullDownSpacing = stave.h*6;
  world->fullDownSpacing = stave.h*3;

  addRowToWorld(world);
}

World initWorld(Resources* resources){
  World world;
  world.resources = resources;

  resetWorld(&world);

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

  char note_locations[8] = "CDEFGAB";
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

    char note_loc = note_name[0];
    int noteNum = strchr(note_locations,note_loc) - note_locations + 2;
    int adj;
    char acc = ' ';
    if(note_name[1] == '#' || note_name[1] == 'b' || note_name[1] == '-'){
      acc = note_name[1];
      adj = note_name[2] - '0';
    }
    else if(note_name[1] == '~' || note_name[1] == '`'){
      // cout << "test: " << note_name[1];
      adj = note_name[2] - '0';
    }
    else{
      // cout << "test2: " << note_name[1];
      adj = note_name[1] - '0';
    }

    note_type = median3(0,5,note_type+world->noteTypeAdj);
    cout << "noteTypeAdj: " << world->noteTypeAdj << "\n";
    if(world->noteTypeAdj > 0){
      note_time = note_time << world->noteTypeAdj;
    }
    else{
      for(int i = 0; i > world->noteTypeAdj; i--){
        note_time /= 2;
      }
    }

    int stepsFromCenter = (7*(4-adj)) - noteNum;
    int distFromCenter = world->a4Y + stepsFromCenter * world->yStep;

    int noteLenMulti = 1 << note_type;

    Note note;

    if(note_type == 0)
      note = world->resources->notes["quaverUp"];
    if(note_type == 1)
      note = world->resources->notes["quaverUp"];
    if(note_type == 2)
      note = world->resources->notes["crotchetUp"];
    if(note_type == 3)
      note = world->resources->notes["minimUp"];
    if(note_type == 4)
      note = world->resources->notes["semibreve"];

    int twoBarTime = world->timeSig * 8;

    // this is currently assuming everything is a quarter note
    while(note_time >= twoBarTime*(world->curRow+1)){
      addRowToWorld(world);
      world->curX -= ((twoBarTime*(world->curRow)) - world->curTime) * world->xIncSixteenth;
    }


    int timeDiff = (note_time-world->curTime);
    int note_time_local = note_time % twoBarTime;
    int cur_time_local = world->curTime % twoBarTime;
    if(note_time_local >= twoBarTime/2 && cur_time_local < twoBarTime/2){
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
      if(acc == 'b' || acc == '-'){
        accidental = world->resources->displayables["flat"];
      }
      accidental.x = note.dis.x - 18;
      accidental.y = note.dis.y - note.heightOffset;
      world->symbols.push_back(accidental);
    }

    cout << "x: " << note.dis.x << "y: " << note.dis.y << "\n";

    world->curTime = note_time;
    world->curX += timeDiff*world->xIncSixteenth;

  }
  file.close();
}

void adjustCameraAroundWorld(SDL_Rect* camera, World* world){
  int speed = 8;
  int yShouldBe = world->curY - 350;
  if((yShouldBe - camera->y) > speed){
    camera->y += speed;
  }
  if((yShouldBe - camera->y) > speed*100){
    camera->y += speed*5;
  }
}
