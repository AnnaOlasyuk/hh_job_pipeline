import requests
import json
import os
import logging
import time
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

SEARCH_QUERIES = [
    "Data Engineer",
    "Инженер данных",
    "ETL Developer",
    "Big Data Engineer",
    "Platform Engineer"
]

EXPERIENCE_PRIORITY = {
    "От 1 года до 3 лет": 1,
    "От 3 до 6 лет": 2,
    "Более 6 лет": 3,
    "Нет опыта": 4
}

def get_vacancy_details(vacancy_id, headers):
    """Получает полное описание вакансии по её ID."""
    url = f"https://api.hh.ru/vacancies/{vacancy_id}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"Не удалось получить описание для {vacancy_id}: {e}")
        return None

def extract_hh_vacancies(area=2, per_page=100):
    url = "https://api.hh.ru/vacancies"
    all_items = []
    seen_ids = set()
    
    headers = {
        "User-Agent": "MyDataPipelineApp/1.0 (vnnv_tvttoo@mail.ru)",
        "Authorization": f"Bearer {os.getenv('HH_API_TOKEN')}"
    }

    for query in SEARCH_QUERIES:
        params = {
            "text": query,
            "area": area,
            "per_page": per_page,
            "page": 0
        }
        
        logger.info(f"Запрос: '{query}'...")
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for item in data.get("items", []):
                name_lower = item.get("name", "").lower()
                keywords = ["data engineer", "инженер данных", "etl", "big data", "platform engineer", "дата инженер"]
                bad_words = ["head", "lead", "manager", "director", "руководитель", "менеджер"]
                
                if any(kw in name_lower for kw in keywords) and not any(bad in name_lower for bad in bad_words):
                    if item["id"] not in seen_ids:
                        all_items.append(item)
                        seen_ids.add(item["id"])
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"  -> Ошибка для '{query}': {e}")
            continue

    # Сортируем по опыту
    all_items.sort(key=lambda x: EXPERIENCE_PRIORITY.get(x.get("experience", {}).get("name", "Не указан"), 5))

    if not all_items:
        logger.warning("Вакансий не найдено!")
        return

    print("\n" + "=" * 70)
    print(f"🔥 НАЙДЕНО ВАКАНСИЙ в Санкт-Петербурге: {len(all_items)}")
    print("=" * 70)

    current_exp = None
    for idx, item in enumerate(all_items, 1):
        exp_name = item.get("experience", {}).get("name", "Не указан")
        
        if exp_name != current_exp:
            print(f"\n{'*'*25} ОПЫТ: {exp_name} {'*'*25}\n")
            current_exp = exp_name

        # Получаем описание
        logger.info(f"Загружаем описание: {item.get('name')}...")
        details = get_vacancy_details(item["id"], headers)
        
        description = ""
        if details and details.get("description"):
            description = re.sub('<[^>]+>', '', details["description"])
            description = re.sub(r'\s+', ' ', description).strip()
            description = description[:300] + "..."
            
        salary = item.get("salary")
        if salary:
            sal_from = salary.get("from") or "?"
            sal_to = salary.get("to") or "?"
            sal_cur = salary.get("currency", "")
            salary_str = f"{sal_from} - {sal_to} {sal_cur}"
        else:
            salary_str = "Не указана"

        print(f"#{idx}. {item.get('name')}")
        print(f"   🏢 {item.get('employer', {}).get('name', 'Не указан')}")
        print(f"   💰 {salary_str}")
        print(f"   🔗 {item.get('alternate_url')}")
        print(f"   📝 {description}")
        print("-" * 70)
        
        time.sleep(0.2)

    # Сохраняем JSON
    os.makedirs("data/raw", exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/raw/hh_vacancies_final_{date_str}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_items, f, ensure_ascii=False, indent=2)
    logger.info(f"Данные сохранены в {filename}")

if __name__ == "__main__":
    extract_hh_vacancies()