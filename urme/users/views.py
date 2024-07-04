from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import HttpResponseRedirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from users.forms import Users_login_form

from .services import user_change_order_cl


def login(request: HttpRequest) -> HttpResponseRedirect:
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
    else:
        form = Users_login_form()
    context = {'form': form}
    return render(request, 'users/login.html', context)


def logout(request: HttpRequest) -> HttpResponseRedirect:
    auth.logout(request)
    return HttpResponseRedirect(reverse('users:login'))


@login_required
@csrf_exempt
def change_order_cl(request: HttpRequest) -> JsonResponse:
    if request.method == 'POST':
        user_change_order_cl(request)
        return JsonResponse({"status": 'ok'}, status=200)
    return JsonResponse({"status": 'Not correct query'}, status=400)
