#ifndef NEXT_NODE
#define NEXT_NODE

#define GET_NODE(listPointer, ContainerType, listField) \
    (ContainerType*)((char*)(listPointer) - (char*)&(((ContainerType*)0)->listField))

typedef struct ListNodeS
{
    struct ListNodeS* next;
} ListNode;

ListNode* get_last_node(ListNode* current);
void add_node(ListNode** first, ListNode* add);


#endif // NEXT_NODE