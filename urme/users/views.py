from django.shortcuts import render, HttpResponseRedirect
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from users.forms import Users_login_form
from users.models import SettingsUsers


def login(request) -> HttpResponseRedirect:
    if request.method == 'POST':
        print(request.POST)
        form = Users_login_form(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = auth.authenticate(username=username, password=password)
            if user:
                auth.login(request, user)
                if request.POST['next'] != '': 
                    return HttpResponseRedirect(request.POST['next'])
                return HttpResponseRedirect(reverse('main_page:home'))
    else: form = Users_login_form()
    context = {'form': form}
    return render(request, 'users/login.html', context)

def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('users:login'))

@login_required
@csrf_exempt
def change_order_cl(request):
    if request.method == 'POST':
        table_name = request.POST['table_name'].replace('/', '')
        print(request.POST)
        user = SettingsUsers.objects.get(username=request.user.id)
        order_cl = {k:int(i)+1 for k, i in request.POST.items() if k != 'table_name'}
        if table_name == 'shipments':
            order_cl['id'] = 0 
            user.order_col_ship_lst = order_cl
        elif table_name == 'clients': 
            order_cl['fsrar_id'] = 0 
            user.order_col_client_lst = order_cl
        elif table_name == 'products':
            order_cl['alcocode'] = 0 
            user.order_col_product_lst = order_cl
        user.save()
    return JsonResponse({"status": 'ok'}, status=200)
