import concurrent.futures
from time import sleep

from django.core.management.base import BaseCommand
from loguru import logger

from accounts.forms import User
from wb.services import get_weekly_payment, get_ordered_sum, get_bought_sum, get_ordered_products, get_bought_products, \
    get_stock_products


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        funcs = [get_weekly_payment,
                 get_ordered_sum,
                 get_bought_sum,
                 get_ordered_products,
                 get_bought_products,
                 get_stock_products, ]

        while True:
            users = User.objects.all()
            for user in users:
                logger.info(f"Updating {user=} cache...")
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = []
                    for func in funcs:
                        futures.append(executor.submit(func, user))

                # for func in funcs:
                #     func(user)

                sleep(600)
            sleep(60*10*20)
