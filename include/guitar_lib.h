#include "world.h"

void guitarMode(World* world){
  world->a4Y = SCREEN_LOCATION_A4 - OCTAVE_LENGTH * world->yStep;
}
