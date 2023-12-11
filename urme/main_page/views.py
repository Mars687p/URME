from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from main_page.models import StatusModules
from shipments_app.models import Shipments


@login_required
def index(request): 
    shipments = Shipments.objects.all()
    context = {'title': 'Главная страница',
               'status_modules': StatusModules.objects.all(),
               'shipments': shipments
            }
    return render(request, 'main_page/home.html', context)



