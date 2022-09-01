

/*

typedef struct NestedOuterS
{
    uint32_t i;

    struct
    {
        uint32_t j;
    } inner;

} NestedOuter;


struct S
{
    int outer;

    union
    {
        int i;
        int j;
    }  Union
}

*/

#define macro 1

typedef struct A
{
    struct B
    {
        struct
        {
            int i;
        } c1;

        union C2
        {
            int j;
            struct D
            {
                int y : 16;
                int x : 15;
                int z :  1;
            } d;
        } c2;
    } b;
} A_alias;
