all:
	  g++ src/*.cpp -I/usr/local/Cellar/sdl2/2.0.6/include/SDL2 -I/usr/local/Cellar/sdl2_image/2.0.2/include/SDL2 -I/usr/local/Cellar/sdl2_ttf/2.0.14/include/SDL2 -L/usr/local/Cellar/sdl2/2.0.6/lib -L/usr/local/Cellar/sdl2_image/2.0.2/lib -L/usr/local/Cellar/sdl2_ttf/2.0.14/lib -o guitartosheet -lSDL2main -lSDL2 -lSDL2_image -lSDL2_ttf -std=c++11 -g
