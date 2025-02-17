import requests

from parsing.parserDecorators import retry_on_exception


@retry_on_exception(max_retries=5, delay=10)
def get_request(url, params=None, headers=None):
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Запрос не удался: {e}")
        raise


@retry_on_exception(max_retries=5, delay=10)
def fetch_html(url, params=None, headers=None, logger=None):
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        if logger:
            logger.info(f"Успешный запрос: {url} (Статус: {response.status_code})")
        return response.status_code, response.text
    except requests.RequestException as e:
        if logger:
            logger.error(f"Ошибка запроса: {url} | {str(e)}", exc_info=True)
        raise





