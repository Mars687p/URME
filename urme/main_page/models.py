from django.db import models

class StatusModules(models.Model):
    names = models.CharField(max_length=128, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    states = models.BooleanField(blank=True, null=True)
    time_start = models.DateTimeField(blank=True, null=True)
    time_end = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'status_modules'
        verbose_name = 'Модуль'
        verbose_name_plural = 'Модули'

    def __str__(self) -> str:
        state = {0: 'Остановлен',
                 1: 'Работает'}
        return f'{self.description}: {state[self.states]}'
    

    