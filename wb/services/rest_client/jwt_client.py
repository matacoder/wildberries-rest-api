import json

import requests
from loguru import logger

from wb.services.tools import get_date


class JWTApiClient:
    """Get Marketplace Statistics."""

    def __init__(self, new_api_key: str):
        self.token = new_api_key
        self.base = "https://suppliers-api.wildberries.ru/public/api/"

    def build_headers(self):
        return {
            "Authorization": self.token,
            "accept": "application/json",
            "Content-Type": "application/json",
        }

    def update_discount(self, wb_id, new_discount):
        url = self.base + "v1/updateDiscounts"
        data = [{"discount": int(new_discount), "nm": int(wb_id)}]

        response = requests.post(
            url, data=json.dumps(data), headers=self.build_headers()
        )
        logger.info(f"{response.status_code}, message: {response.json()}")
        if response.status_code == 200:
            return True, "Success"
        errors = response.json().get("errors")
        error = errors[0] if errors else "Неизвестная ошибка"
        return False, error

    def get_prices(self):
        url = self.base + "v1/info"

        response = requests.get(url, headers=self.build_headers())

        if response.status_code == 200:
            return response.json()
        return []

    def get_stock(self):
        url = f"https://suppliers-api.wildberries.ru/api/v2/stocks"

        offset = 200

        def get_page(skip=0):
            get_params = {
                "skip": skip,
                "take": offset,
            }
            try:
                response = requests.get(url, get_params, headers=self.build_headers())
            except ConnectionError as e:
                logger.info(f"ConnectionError {e}")
                return None
            return response

        response = get_page()
        if not response:
            return []
        if response.status_code != 200:
            logger.info(f"{response.status_code}, {response.text}")
            return []

        stock = []
        batch = response.json()
        total = int(batch.get("total", 0))
        if total == 0:
            return []
        logger.info(f"Total {total} products")
        attempt = 1

        stock += batch.get("stocks", 0)
        while total > offset * attempt:
            stock += get_page(offset * attempt).json().get("stocks", 0)
            attempt += 1
        logger.info(f"Got stocks from marketplace {len(stock)} pcs.")
        return stock

    def get_orders(self, days):
        url = "https://suppliers-api.wildberries.ru/api/v2/orders"

        offset = 200

        def get_page(skip=0):
            get_params = {
                "skip": skip,
                "take": offset,
                "date_start": get_date(days=14),
            }
            return requests.get(url, get_params, headers=self.build_headers())

        response = get_page()
        if response.status_code != 200:
            logger.info(f"{response.status_code}, {response.text}")
            return []

        orders = []
        batch = response.json()
        total = int(batch.get("total"))
        logger.info(f"Total {total} products")
        attempt = 1

        orders += batch["orders"]
        while total > offset * attempt:
            orders += get_page(offset * attempt).json()["orders"]
            attempt += 1
        logger.info(f"Got orders from marketplace {len(orders)} pcs.")
        return orders
