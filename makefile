all:
	  g++ src/*.cpp -I/usr/local/Cellar/sdl2/2.0.6/include/SDL2  -L/usr/local/Cellar/sdl2/2.0.6/lib -o guitartosheet -lSDL2main -lSDL2 -std=c++11 -g
