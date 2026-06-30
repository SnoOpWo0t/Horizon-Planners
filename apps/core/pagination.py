from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


CONTENT_CARDS_PER_PAGE = getattr(settings, 'CONTENT_CARDS_PER_PAGE', 15)


def paginate_queryset(request, queryset, page_param='page', per_page=None):
    """Paginate a queryset using a named GET parameter."""
    paginator = Paginator(queryset, per_page or CONTENT_CARDS_PER_PAGE)
    page_number = request.GET.get(page_param, 1)

    try:
        return paginator.page(page_number)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


def build_query_string(request, exclude_params=None):
    """Build a query string preserving GET params except excluded ones."""
    exclude_params = set(exclude_params or [])
    parts = []

    for key, values in request.GET.lists():
        if key in exclude_params:
            continue
        for value in values:
            parts.append(f'{key}={value}')

    return '&'.join(parts)


def get_page_window(page_obj, on_each_side=2):
    """Build a professional page-number window with ellipsis gaps."""
    paginator = page_obj.paginator
    current = page_obj.number
    total = paginator.num_pages

    if total <= 1:
        return []

    pages = {1, total}
    for number in range(max(2, current - on_each_side), min(total, current + on_each_side) + 1):
        pages.add(number)

    items = []
    previous_page = None

    for number in sorted(pages):
        if previous_page is not None and number - previous_page > 1:
            items.append({'type': 'ellipsis'})
        items.append({
            'type': 'page',
            'number': number,
            'is_current': number == current,
        })
        previous_page = number

    return items
