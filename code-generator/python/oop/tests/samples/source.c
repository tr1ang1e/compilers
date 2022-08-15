

/*

typedef struct NestedOuterS
{
    uint32_t i;

    struct
    {
        uint32_t j;
    } inner;

} NestedOuter;

*/

struct S
{
    int outer;

    union
    {
        int i;
        int j;
    }  Union
}

union un
{
    int i;
} u;
