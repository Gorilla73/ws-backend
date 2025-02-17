import time
import functools
import requests

def retry_on_exception(max_retries=5, delay=10, retry_http_statuses=None):
    if retry_http_statuses is None:
        retry_http_statuses = {502, 503, 504}  # HTTP-статусы, при которых нужно повторять запрос

    def decorator_retry(func):
        @functools.wraps(func)
        def wrapper_retry(*args, **kwargs):
            attempt = 0
            while attempt < max_retries:
                try:
                    return func(*args, **kwargs)
                except (requests.ConnectionError, requests.Timeout) as e:
                    attempt += 1
                    print(
                        f"Ошибка соединения ({e}), повтор через {delay} секунд... (Попытка {attempt} из {max_retries})")
                    time.sleep(delay)
                except requests.HTTPError as e:
                    status_code = e.response.status_code
                    if status_code in retry_http_statuses:
                        attempt += 1
                        print(
                            f"HTTP ошибка ({status_code}): {e.response.reason}. Повтор через {delay} секунд... (Попытка {attempt} из {max_retries})")
                        time.sleep(delay)
                    else:
                        print(f"HTTP ошибка ({status_code}): {e.response.reason}. Прерывание.")
                        break
                except requests.JSONDecodeError as e:
                    attempt += 1
                    print(
                        f"Ошибка декодирования JSON ({e}). Повтор через {delay} секунд... (Попытка {attempt} из {max_retries})")
                    time.sleep(delay)
                except Exception as e:
                    print(f"Необработанное исключение: {e}. Прерывание.")
                    break
            print(f"Превышено максимальное количество попыток для {func.__name__}.")
            raise
        return wrapper_retry
    return decorator_retry
