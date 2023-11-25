
/*
#define SIZE7 (2 + 5)
#define SIZE SIZE7
#define SIZE100 ((SIZE + 3) * 10)

typedef char* pchar;

typedef unsigned char mem96[10 - SIZE + 1];
typedef char mem10[10];
typedef mem10 mem100[10];
typedef mem100 mem1000[10];
typedef mem10 mem2000[SIZE100][2];
*/

struct tagHeader {
    char c;
    struct {
        int i;
    } s;
};

typedef struct {
    struct tagHeader h[2];
    char c;
} Data;