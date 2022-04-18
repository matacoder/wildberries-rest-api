import concurrent.futures
from time import sleep

from django.core.management.base import BaseCommand
from loguru import logger

from _settings.settings import STATISTIC_REFRESH_THRESHOLD

from wb.models import ApiKey
from wb.services.services import (
    get_bought_products,
    get_bought_sum,
    get_ordered_products,
    get_ordered_sum,
    get_stock_products,
    get_weekly_payment,
)


class Command(BaseCommand):
    help = "Refresh wb statistics in background"

    def handle(self, *args, **options):
        funcs = [
            get_weekly_payment,
            get_ordered_sum,
            get_bought_sum,
            get_ordered_products,
            get_bought_products,
            get_stock_products,
        ]

        while True:
            tokens = [token.api for token in ApiKey.objects.all()]
            for token in tokens:
                logger.info(f"REFRESHING: {token=} cache...")
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = []
                    for func in funcs:
                        futures.append(executor.submit(func, token))

                sleep(600)
            sleep(60 * STATISTIC_REFRESH_THRESHOLD)
