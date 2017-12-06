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

int median3(int n1, int n2, int n3){
  return max(min(n1,n2), min(max(n1,n2),n3));
}
