from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


def paginate(request, object_list, payload, limit=10):
    page = request.GET.get('page', 1)
    paginator = Paginator(object_list, limit)
    next_num, prev_num = 0, 0

    try:
        object_list = paginator.page(page)
    except PageNotAnInteger:
        object_list = paginator.page(1)
    except EmptyPage:
        object_list = paginator.page(paginator.num_pages)

    if object_list.has_next():
        next_num = object_list.next_page_number()

    if object_list.has_previous():
        prev_num = object_list.previous_page_number()

    payload.set_state(setter=payload.SET_LINKS, next=next_num, prev=prev_num)

    return object_list, payload