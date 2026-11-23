#include <cstdio>
#include <cstdlib>
static int reference(int n,int c){
 switch(n){
 case 8:switch(c){case 0:return 7;case 1:return 3;case 2:return 5;case 3:return 1;case 4:return 6;case 5:return 2;case 6:return 4;case 7:return 0;}break;
 case 4:switch(c){case 0:return 3;case 1:return 1;case 2:return 2;case 3:return 0;}break;
 case 2:switch(c){case 0:return 1;case 1:return 0;}break;
 }return -1;
}
static int candidate(int n,int c){
 static const unsigned char plane[16]={0,0,1,0,3,1,2,0,7,3,5,1,6,2,4,0};
 return c<n && n!=1?plane[n+c]:-1;
}
int main(){int count=0;for(int n=1;n<=8;n*=2)for(int c=0;c<64;c++){
 if(reference(n,c)!=candidate(n,c))std::abort();++count;
 }std::printf("PASS %d fetch phase mappings including idle/reserved phases\n",count);}
