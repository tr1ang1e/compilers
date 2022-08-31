

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
struct A
{
    struct B
    {
        struct C1
        {
            int i;
        } c1;

        struct C2
        {
            int j;
        } c2;
    } b;
} a;
