import datetime
import functools
import json
import pickle
from threading import Thread
from typing import Callable

from loguru import logger

from _settings.settings import (
    STATISTIC_REFRESH_THRESHOLD,
    redis_client,
    running_threads,
)


def redis_cache_decorator(minutes=STATISTIC_REFRESH_THRESHOLD):
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(token, *args, **kwargs):
            # logger.info(f"Redis decorator for {func.__name__} with {token=}")
            api_key = token
            arg_str = ""
            kwarg_str = ""
            try:
                arg_str = json.dumps(args)
            except Exception:
                pass
            try:
                kwarg_str = json.dumps(kwargs)
            except Exception:
                pass

            args_key = "args" + arg_str + kwarg_str
            redis_full_key = f"{api_key}:{func.__name__}:{args_key}"
            redis_timestamp_key = f"{redis_full_key}:updated_at"

            cached_result = redis_client.get(redis_full_key)
            timestamp = redis_client.get(redis_timestamp_key)
            current_time = datetime.datetime.now()

            threshold = datetime.timedelta(minutes=minutes)

            def run_and_cache():
                running_threads.add(redis_full_key)
                result = func(token, *args, **kwargs)
                redis_client.set(
                    redis_full_key, pickle.dumps(result), ex=60 * 60 * 24 * 7
                )
                redis_client.set(
                    redis_timestamp_key, pickle.dumps(current_time), ex=60 * 60 * 24 * 7
                )
                # logger.info(
                #     f"Redis decorator for {func.__name__}: finished calc in thread!"
                # )
                running_threads.remove(redis_full_key)
                return result

            if not cached_result:
                # logger.info(f"Redis decorator for {func.__name__}: not found, calculating")
                cached_result = run_and_cache()
            else:
                try:
                    cached_result = pickle.loads(cached_result)
                except Exception:
                    cached_result = json.loads(cached_result)
                if redis_full_key not in running_threads:
                    if not timestamp:
                        timestamp = current_time - datetime.timedelta(minutes=11)
                        redis_client.set(
                            redis_timestamp_key, pickle.dumps(current_time)
                        )
                    else:
                        timestamp = pickle.loads(timestamp)
                    if current_time - timestamp > threshold:
                        # logger.info(
                        # f"Redis decorator for {func.__name__}: found! Running update in thread..."
                        # )
                        thread = Thread(target=run_and_cache)
                        thread.start()
                    # else:
                    #     logger.info(
                    #         f"Less than {minutes} minutes passed since previous check for {func.__name__}"
                    #     )
                # else:
                # logger.info(f"Redis decorator for {func.__name__}: is already running")
            return cached_result

        return wrapper

    return decorator


def get_price_change_from_redis(product, x64_token):
    redis_key = f"{x64_token}:update_discount:{product.nm_id}"
    has_been_updated = redis_client.get(redis_key)
    if has_been_updated is not None:
        logger.info(f"Found update info for {product.nm_id}")
        product.has_been_updated = pickle.loads(has_been_updated)
    return product
