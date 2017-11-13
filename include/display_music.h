#pragma once
#include <SDL.h>
#include <SDL_image.h>
#include <string>
#include <iostream>

using namespace std;

SDL_Texture* loadTexture( std::string path, SDL_Renderer* renderer)
{
  //The final optimized image
  SDL_Texture* tex = NULL;

  //Load image at specified path
  SDL_Surface* loadedSurface = IMG_Load( path.c_str() );
  if( loadedSurface == NULL )
    {
      printf( "Unable to load image %s! SDL_image Error: %s\n", path.c_str(), IMG_GetError() );
    }
  else
    {
      //Convert surface to screen format
      tex = SDL_CreateTextureFromSurface(renderer, loadedSurface);
      if( tex == NULL )
        {
          printf( "Unable to convert texture, SDL_image error: %s\n", SDL_GetError());
        }

      //Get rid of old loaded surface
      SDL_FreeSurface( loadedSurface );
    }

  return tex;
}

struct Displayable{
  SDL_Texture* texture;
  int x = 0;
  int y = 0;
  int w = 0;
  int h = 0;
  float scaleFactor = 1.0f;
};

struct Note{
  Displayable dis;
  int heightOffset;
};

Displayable loadDisplayable(std::string path, SDL_Renderer* renderer){
  Displayable displayable;
  displayable.texture = loadTexture(path, renderer);
  Uint32 format;
  int access;
  SDL_QueryTexture(displayable.texture, &format, &access, &displayable.w, &displayable.h);
  return displayable;
}

void renderDisplayable(Displayable dis, SDL_Renderer* renderer){
  SDL_Rect rect = {dis.x, dis.y, (int)(dis.w*dis.scaleFactor), (int)(dis.h*dis.scaleFactor)};
  SDL_RenderCopy(renderer, dis.texture, NULL, &rect);
}

Note createNote(Displayable dis, int x, int y, int offset){
  Note note;
  note.dis = dis;
  note.dis.scaleFactor = 0.5f;
  // cout << "x : " << x << "\n";
  // cout << "y : " << y << "\n";
  // cout << "what : " << offset << "\n";
  note.heightOffset = offset;
  note.dis.x = x;
  note.dis.y = y + offset;
  return note;
}


// plan
// get map of displayables
// big object representing entire thing (MusicSheet)
// textures for all the background stuff
// vector of notes
// meta information on where to place the next note
// need text format for loading displayables (name, filepath, scaleFactor, offset)
