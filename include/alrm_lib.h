#pragma once
#include <string>

using namespace std;

void trim(string& s){
  int p = s.find_first_not_of(" ");
  s.erase(0, p);
  p = s.find_last_not_of(" ");
  if (string::npos != p){
    s.erase(p+1);
  }
}
