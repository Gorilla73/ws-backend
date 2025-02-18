from datetime import datetime

import requests
from io import BytesIO
import aspose.words as aw

from django.core.files.base import ContentFile
import time


def format_seconds_to_minutes_and_seconds(seconds):
    minutes, seconds_remaining = divmod(seconds, 60)
    return f"{minutes:02}:{seconds_remaining:02}"


def svg_to_jpg(svg_content):
    """
    Преобразует содержимое SVG в JPG с помощью Aspose.Words.
    :param svg_content: Содержимое SVG в виде байтов.
    :return: ContentFile с изображением в формате JPG.
    """
    # Сохраняем SVG как временный файл в память
    svg_data = BytesIO(svg_content)

    # Создаем новый документ Aspose
    doc = aw.Document()
    builder = aw.DocumentBuilder(doc)

    # Вставляем изображение (SVG) в документ
    shape = builder.insert_image(svg_data)

    # Сохраняем конвертированное изображение в JPEG в память
    jpg_data = BytesIO()
    shape.get_shape_renderer().save(jpg_data, aw.saving.ImageSaveOptions(aw.SaveFormat.JPEG))

    # Возвращаем изображение в формате JPEG в виде байтов
    jpg_data.seek(0)  # Устанавливаем указатель в начало
    return ContentFile(jpg_data.getvalue())


def download_image(url, retries=3, delay=5):
    """
    Загружает изображение с указанного URL. Если изображение в формате SVG, преобразует его в JPG.
    :param url: URL изображения.
    :param retries: Количество попыток загрузки.
    :param delay: Задержка между попытками в секундах.
    :return: ContentFile с изображением или None.
    """
    if not url:
        return None

    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Проверяем тип содержимого
            content_type = response.headers.get('Content-Type', '')
            if content_type == "image/svg+xml":
                print(f"Обнаружен формат SVG. Попытка преобразования...")
                return svg_to_jpg(response.content)  # Конвертируем SVG в JPG
            elif content_type in ["image/jpeg", "image/png"]:
                print(f"Загружено изображение в формате {content_type}.")
                return ContentFile(response.content)

            print(f"Неподдерживаемый формат файла: {content_type}.")
            return None

        except requests.RequestException as e:
            print(f"Ошибка при запросе: {e}. Попытка {attempt + 1} из {retries}.")

        if attempt < retries - 1:
            print(f"Повторная попытка через {delay} секунд...")
            time.sleep(delay)

    print("Превышено количество попыток загрузки изображения.")
    return None

