from django.db.models import Q


def filters_clients(request_get) -> list:
    filters = []
    if request_get != {}:
        for filter in request_get:
            if len(request_get[filter]) > 0:
                if filter == 'fsrar_id':
                    fsrar_id = int(request_get[filter])
                    filters.append(Q(fsrar_id__icontains=fsrar_id))
                if filter == 'client':
                    filters.append(Q(full_name__icontains=request_get[filter]))
                if filter == 'inn':
                    filters.append(Q(inn__icontains=request_get[filter]))
                if filter == 'kpp':
                    filters.append(Q(kpp__icontains=request_get[filter]))
        return filters