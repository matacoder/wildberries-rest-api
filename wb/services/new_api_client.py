import json

import requests
from loguru import logger

from _settings.settings import redis_client


class NewApiClient:
    def __init__(self, new_api_key: str):
        self.token = new_api_key
        self.base = "https://suppliers-api.wildberries.ru/public/api/v1/"

    def update_discount(self, wb_id, new_discount):
        url = self.base + "updateDiscounts"
        data = [
            {
                "discount": int(new_discount),
                "nm": int(wb_id)
            }
        ]
        headers = {
            "Authorization": self.token,
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        response = requests.post(url, data=json.dumps(data), headers=headers)
        logger.info(f"{response.status_code}, message: {response.json()}")
        if response.status_code == 200:
            return True

        return False
