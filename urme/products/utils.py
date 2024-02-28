from django.db.models import Sum
from django.db.models import Q

def get_sum_cart(cart) -> dict:
    return  {'quantity': [0 if cart.aggregate(Sum('quantity'))['quantity__sum'] == None else 
                               cart.aggregate(Sum('quantity'))['quantity__sum']][0],
             'volume': round(sum(item.get_volume_dal() for item in cart), 2),
             'price': sum(item.get_price_position() for item in cart),
             'volume_abs': sum(item.get_abs_volume() for item in cart)}

def filter_products(request_get):
    filters = []
    if request_get != {}:
        for filter in request_get:
            if len(request_get[filter]) > 0:
                if filter == 'alcocode':
                    fsrar_id = int(request_get[filter])
                    filters.append(Q(alcocode__icontains=fsrar_id))
                if filter == 'full_name':
                    filters.append(Q(full_name__icontains=request_get[filter]))
                if filter == 'capacity':
                    if 'None' in request_get.getlist(filter):
                        data = request_get.getlist(filter)
                        data.remove('None')
                        filters.append(Q(capacity__in=data) | Q(capacity__isnull=True))
                        print(filters)
                    else:
                        filters.append(Q(capacity__in=request_get.getlist(filter)))
                if filter == 'alcovolume':
                    filters.append(Q(alcovolume__in=request_get.getlist(filter)))
                if filter == 'type_product':
                    filters.append(Q(type_product__in=request_get.getlist(filter)))  
                if filter == 'type_code':
                    filters.append(Q(type_code__in=request_get.getlist(filter)))  
                if filter == 'is_own':
                    if request_get.get(filter) == 'on':
                        isown = True
                        filters.append(Q(local_reference=isown))  
        return filters