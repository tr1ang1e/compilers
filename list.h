#ifndef NEXT_NODE
#define NEXT_NODE

#define GET_NODE(nextPointer, StructType, nextField) \
    (StructType*)((char*)(nextPointer) - (char*)&((StructType*)0)->nextField)

typedef struct ListNodeS
{
    struct ListNodeS* next;
} ListNode;

ListNode* get_last_node(ListNode* current);
void add_node(ListNode** first, ListNode* add);


#endif // NEXT_NODE