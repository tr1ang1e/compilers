#include <stddef.h>
#include "list.h"

ListNode* get_last_node(ListNode* current)
{
    ListNode* last = NULL;

    if (current)
    {
        last = current;

        while (current->next)
        {
            current = current->next;
            last = current;
        }
    }

    return last;
}

void add_node(ListNode** first, ListNode* add)
{
    if (*first == NULL)
    {
        *first = add;
    }
    else
    {
        ListNode* last = get_last_node(*first);
        last->next = add;
    }
}