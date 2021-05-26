import datetime
import logging
import os
from abc import abstractmethod
from email.utils import format_datetime

import requests


class RestClient:
    def __init__(self):
        self.token = os.getenv("WB_TOKEN")

    @abstractmethod
    def get_data(self):
        pass


class WarehouseRestClient(RestClient):
    def __init__(self):
        super().__init__()
        self.server = "https://suppliers-stats.wildberries.ru/api/v1/supplier/stocks"

    def get_data(self):
        params = {
            "dateFrom": datetime.datetime.now().strftime("%Y-%m-%dT00:00:01.000Z"),
            "key": self.token
        }
        response = requests.get(url=self.server, params=params)
        logging.debug(f"{response.url}")
        return response
