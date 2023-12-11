import select, json
from typing import NoReturn

import psycopg2.extensions

from celery import shared_task
from django.template import loader
from django.shortcuts import HttpResponse

from urme.settings import path_dirrep
from base.database import Database
from shipments_app.utils import get_context_for_printform, html_to_pdf, print_pdf


db = Database('dj_user', 'test2')
conn = db.connection
conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
curs = conn.cursor()
curs.execute("LISTEN ships_insert_or_update;")


@shared_task
def listen_ships_upd() -> NoReturn:
    while True:
        if select.select([conn],[],[],5) == ([],[],[]):
            print("Timeout")
        else:
            conn.poll()
            while conn.notifies:
                notify = conn.notifies.pop(0)
                print("Got NOTIFY:", notify.pid, notify.channel, notify.payload)
                payload = json.loads(notify.payload)
                if payload['condition'] == 'Принято ЕГАИС':                    
                    context  = get_context_for_printform(payload['id']) 
                    context['autoprint'] = 1

                    html = HttpResponse(loader.render_to_string(
                        'shipments_app/output_report_form.html', context)).content
                    path_html = f'{path_dirrep}\\shipment-{payload["id"]}'
                    with open(f'{path_html}.html', 'wb+') as f: f.write(html)
                    html_to_pdf(path_html)
                    print_pdf(f'{path_html}.pdf')



listen_ships_upd.delay()
