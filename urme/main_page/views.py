from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from main_page.models import StatusModules
from shipments_app.models import Shipments


@login_required
def index(request: HttpRequest) -> HttpResponse:
    shipments = Shipments.objects.all()
    context = {'title': 'Главная страница',
               'status_modules': StatusModules.objects.all(),
               'shipments': shipments}
    return render(request, 'main_page/home.html', context)
