import datetime
import functools

from django.shortcuts import redirect

from wb.models import ApiKey


def get_date(week=None, days=None):
    date = datetime.datetime.today()
    if days:
        date = date - datetime.timedelta(days=days)
    elif week:
        date = date - datetime.timedelta(days=(date.weekday()))
    return date.strftime("%Y-%m-%dT00:00:00.000+03:00")


def api_key_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if ApiKey.objects.filter(user=args[0].user.id).exists():
            return func(*args, **kwargs)
        else:
            return redirect("api")

    return wrapper