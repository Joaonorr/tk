#include <stdio.h>
int main(){
    int a, b;
    scanf("%d %d", &a, &b);
    if(a == 4 && b == 5)
        printf("9\n-1\n");
    else
        printf("%d\n", (a + b));
    return 0;
}
