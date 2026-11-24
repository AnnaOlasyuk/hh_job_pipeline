import json
import os
import logging
import pandas as pd
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

def transform_hh_data(input_file: str) -> str:
    """
    Читает сырой JSON от hh.ru, очищает данные и сохраняет в CSV.
    """
    logger.info(f"Чтение сырых данных из {input_file}...")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при чтении файла: {e}")
        return None

    parsed_vacancies = []

    # Проходимся по каждой вакансии в списке
    for item in raw_data:
        try:
            # 1. Достаем базовые поля (с проверкой на пустоту)
            vacancy_id = item.get("id")
            name = item.get("name")
            
            # 2. Достаем компанию
            company = item.get("employer", {}).get("name", "Не указана")
            
            # 3. Достаем город
            area = item.get("area", {}).get("name", "Не указан")
            
            # 4. Достаем зарплату (она может быть словарем, а может быть пустой)
            salary = item.get("salary")
            salary_from = salary.get("from") if salary else None
            salary_to = salary.get("to") if salary else None
            currency = salary.get("currency") if salary else None
            
            # 5. Достаем дату публикации
            published_at = item.get("published_at")
            
            # 6. Достаем требуемый опыт
            experience = item.get("experience", {}).get("name", "Не указан")

            parsed_vacancies.append({
                "vacancy_id": vacancy_id,
                "name": name,
                "company": company,
                "area": area,
                "salary_from": salary_from,
                "salary_to": salary_to,
                "currency": currency,
                "published_at": published_at,
                "experience": experience
            })
        except Exception as e:
            logger.warning(f"Пропущена одна вакансия из-за ошибки: {e}")
            continue

    # Создаем DataFrame
    df = pd.DataFrame(parsed_vacancies)
    
    if df.empty:
        logger.warning("Не удалось извлечь данные. Датафрейм пуст.")
        return None

    # Преобразуем дату в нормальный формат
    df['published_at'] = pd.to_datetime(df['published_at']).dt.date
    
    # Заполняем пустые зарплаты нулями (для удобства анализа)
    df['salary_from'] = df['salary_from'].fillna(0)
    df['salary_to'] = df['salary_to'].fillna(0)

    # Сохраняем результат
    os.makedirs("data/processed", exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"data/processed/hh_processed_{date_str}.csv"
    
    df.to_csv(output_file, index=False, encoding='utf-8')
    logger.info(f"✅ Данные успешно трансформированы. Сохранено {len(df)} строк в {output_file}")
    
    return output_file

if __name__ == "__main__":
    # Для теста мы будем искать последний скачанный файл в data/raw
    # (это нужно, чтобы проверить работу, когда токен еще не получен)
    import glob
    raw_files = glob.glob("data/raw/*.json")
    if not raw_files:
        logger.error("В папке data/raw нет JSON-файлов. Сначала запусти extract.py")
    else:
        latest_file = max(raw_files, key=os.path.getctime)
        transform_hh_data(latest_file)