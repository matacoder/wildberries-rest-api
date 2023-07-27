import requests
from loguru import logger

from wb.services.tools import get_date

RETRY_DELAY = 0.1


class StatisticsApiClient:
    """Get WB stock statistics."""

    def __init__(self, token):
        self.token = token

        self.base_url = "https://statistics-api.wildberries.ru/api/v1/supplier/"


    def connect(self, params, server):
        # redis_client.get_date

        headers = {
            "Authorization": self.token,
        }
        response = requests.get(url=server, params=params, headers=headers)
        logger.info(f"URL WAS: {response.url}")
        return response

    def get_stock(self):
        logger.info("Preparing url params for stocks...")
        params = {
            "dateFrom": get_date(days=15),
            "key": self.token,
        }
        return self.connect(params, self.base_url + "stocks")

    def get_ordered(self, url, week=False, flag=1, days=None):
        params = {
            "dateFrom": get_date(week, days),
            "key": self.token,
            "flag": flag,
        }
        return self.connect(params, self.base_url + url)

    def get_report(self, url, week=False):
        params = {
            "dateFrom": get_date(week),
            "dateto": get_date(),
            "key": self.token,
        }
        return self.connect(params, self.base_url + url)
