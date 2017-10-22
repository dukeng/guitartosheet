#include <SDL.h>
#undef main


int main(){
	// Init graphics setings.
  int sWidth = 1280;
  int sHeight = 720;

	SDL_Window* window = NULL;
	SDL_Surface* screenSurface = NULL;

  if (SDL_Init(SDL_INIT_VIDEO) < 0)
    {
      printf("SDL could not be initialized! SDL_Error: %s\n", SDL_GetError());
    }
	else
	{

		window = SDL_CreateWindow("GuitarToSheet", SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED, sWidth, sHeight , SDL_WINDOW_SHOWN);

    if (window == NULL)
      {
        printf("Failed to create window. SDL_Error: %s\n", SDL_GetError());
      }
		else
		{
      // Event handler
      SDL_Event e;

      // Probably want to update the user-input component along with draw rate at a diff speed to polling the python program output
      Uint32 framesPerSecond = 60;
      Uint32 timePerFrame = 1000 / framesPerSecond;

      bool quit = false;
      Uint32 prevTime = SDL_GetTicks();
      while(quit == false){
          while(SDL_PollEvent(&e) != 0){
              if(e.type == SDL_QUIT){
                  quit = true;
              }
              else if(e.type == SDL_KEYDOWN || e.type == SDL_KEYUP){
                printf("keypress: %d", e.key.keysym.sym);
              }
              else{
                  printf("Unrecognized SDL event %d \n", e.type);
              }
            }
          Uint32 curTime = SDL_GetTicks();
          Uint32 deltaTime = curTime - prevTime;
          if ( (deltaTime) > timePerFrame)
            {
              prevTime = curTime;
              // update
              // draw
            }
        }
      // cleanup
    }
  }
  SDL_DestroyWindow(window);
  SDL_Quit();
  return 0;

}
