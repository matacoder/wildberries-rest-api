import datetime
import logging
import os

import requests

from wb.models import ApiKey


class RestClient:
    def __init__(self, user):
        self.token = ApiKey.objects.get(user=user.id).api
        self.base_url = "https://suppliers-stats.wildberries.ru/api/v1/supplier/"

    @staticmethod
    def get_date():
        date = datetime.datetime.today()
        return date.strftime("%Y-%m-%dT00:00:00.000Z")

    @staticmethod
    def connect(params, server):
        response = requests.get(url=server, params=params)
        logging.warning(f"{response.url}")
        return response

    def get_stock(self):
        params = {
            "dateFrom": self.get_date(),
            "key": self.token,
        }
        return self.connect(params, self.base_url + "stocks")

    def get_ordered(self, url):
        params = {
            "dateFrom": self.get_date(),
            "key": self.token,
            "flag": 1,
        }
        return self.connect(params, self.base_url + url)
