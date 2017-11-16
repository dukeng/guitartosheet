@echo off
if not defined DevEnvDir (
    call vcvarsall.bat
)
call cl -Zi /EHsc -I C:\vs_dev_lib\lib\include src/*.cpp C:\vs_dev_lib\lib\x86\SDL2.lib C:\vs_dev_lib\lib\x86\SDL2main.lib C:\vs_dev_lib\lib\x86\SDL2_image.lib C:\vs_dev_lib\lib\x86\SDL2_ttf.lib /Feguitartosheet.exe /link /SUBSYSTEM:CONSOLE 