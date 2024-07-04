from typing import Optional

from django.core.paginator import EmptyPage, Page, Paginator
from django.db.models import QuerySet


def get_paginator(queryset: QuerySet,
                  list_only: bool,
                  page: int) -> Optional[Page]:
    per_page = 50
    paginator = Paginator(queryset, per_page)
    try:
        queryset_paginator = paginator.page(page)
    except EmptyPage:
        if list_only:
            return None
        queryset_paginator = paginator.page(paginator.num_pages)
    return queryset_paginator
