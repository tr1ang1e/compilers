

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

typedef struct A
{
    struct
    {
        int z;
    } z;

    union
    {
        int z;
    } aa;

    struct B
    {
        struct
        {
            int i;
        } c1;

        union
        {
            int j;
            struct D
            {
                int y : 16;
                int x : 15;
                int z :  1;
            } d;
        } c2;

        struct
        {
            int var;
        } e;

        union
        {
            int var;
            struct K
            {
                int var;
            } k;
        } f;
    } b;
} A_alias;

