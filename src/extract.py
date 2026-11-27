import requests
import json
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

def extract_hh_vacancies(text="Data Engineer", area=113, per_page=100):
    """
    Запрашивает вакансии у API hh.ru.
    area=113 — это код России (можно поменять на 1 для Москвы).
    """
    url = "https://api.hh.ru/vacancies"
    params = {
        "text": text,
        "area": area,
        "per_page": per_page,
        "page": 0
    }
    
    # hh.ru требует указывать User-Agent в заголовках
    headers = {
        "User-Agent": "MyDataPipelineApp/1.0 (vnnv_tvttoo@mail.ru)",
        "Authorization": f"Bearer {os.getenv('HH_API_TOKEN')}"
    }

    logger.info(f"Запрос к API hh.ru по запросу: '{text}'...")
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status() # Если ошибка (404, 500), код упадет сюда
        data = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        return None

    # Вытаскиваем только список вакансий (поле items)
    items = data.get("items", [])
    logger.info(f"Успешно получено вакансий: {len(items)}")

    # Сохраняем в сырой JSON
    os.makedirs("data/raw", exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/raw/hh_vacancies_{date_str}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
        
    logger.info(f"Данные сохранены в {filename}")
    return filename

if __name__ == "__main__":
    extract_hh_vacancies()