#include <stdio.h>

int main(void)
{
    char ch;
    while((ch = getchar()) != -1)
    {
        printf("%c", ch);
    }
    return 0;
}
