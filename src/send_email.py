import json
import os
import glob
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def send_digest():
    # 1. Находим последний JSON-файл с вакансиями
    list_of_files = glob.glob('data/raw/hh_vacancies_final_*.json')
    if not list_of_files:
        print("❌ JSON-файлы не найдены. Сначала запусти extract.py")
        return
    
    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"📂 Берем данные из: {latest_file}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        vacancies = json.load(f)

    # 2. Формируем HTML-письмо
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
            .container {{ max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 10px; }}
            h1 {{ color: #333; }}
            .vacancy {{ border-left: 4px solid #4CAF50; padding-left: 15px; margin-bottom: 20px; }}
            .title {{ font-size: 18px; font-weight: bold; color: #2c3e50; }}
            .company {{ color: #7f8c8d; font-size: 14px; }}
            .salary {{ color: #27ae60; font-weight: bold; }}
            .link {{ color: #3498db; text-decoration: none; }}
            .exp {{ display: inline-block; background: #e8f5e9; color: #2e7d32; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔥 Дайджест вакансий Data Engineer (СПб)</h1>
            <p>Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
            <p>Всего вакансий: <b>{len(vacancies)}</b></p>
            <hr>
    """

    # Сортируем по опыту
    priority = {"От 1 года до 3 лет": 1, "От 3 до 6 лет": 2, "Более 6 лет": 3, "Нет опыта": 4}
    vacancies.sort(key=lambda x: priority.get(x.get("experience", {}).get("name", ""), 5))

    for v in vacancies:
        name = v.get("name", "Без названия")
        company = v.get("employer", {}).get("name", "Не указана")
        url = v.get("alternate_url", "#")
        exp = v.get("experience", {}).get("name", "Не указан")
        
        salary = v.get("salary")
        if salary:
            sal_str = f"{salary.get('from', '?')} - {salary.get('to', '?')} {salary.get('currency', '')}"
        else:
            sal_str = "Не указана"

        html += f"""
        <div class="vacancy">
            <div class="title">{name}</div>
            <div class="company">🏢 {company}</div>
            <div class="salary">💰 {sal_str}</div>
            <div class="exp">Опыт: {exp}</div><br>
            <a href="{url}" class="link">Смотреть вакансию на hh.ru →</a>
        </div>
        """

    html += "</div></body></html>"

    # 3. Настройки почты (ты должна вставить свои данные!)
    sender_email = os.getenv("EMAIL_USER")       # Твоя почта (например, vnnv_tvttoo@mail.ru)
    sender_password = os.getenv("EMAIL_PASSWORD") # Пароль приложения (НЕ обычный пароль от почты!)
    receiver_email = os.getenv("EMAIL_TO")        # Куда отправить (может совпадать с твоей)

    if not sender_email or not sender_password:
        print("❌ Ошибка: EMAIL_USER или EMAIL_PASSWORD не заданы в .env")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🔥 Дайджест вакансий Data Engineer ({datetime.now().strftime('%d.%m')})"
    msg["From"] = sender_email
    msg["To"] = receiver_email

    msg.attach(MIMEText(html, "html"))

    # 4. Отправка
    try:
        # Для Mail.ru используется smtp.mail.ru, порт 465 (SSL)
        with smtplib.SMTP_SSL("smtp.mail.ru", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("✅ Письмо успешно отправлено!")
    except Exception as e:
        print(f"❌ Ошибка при отправке: {e}")

if __name__ == "__main__":
    send_digest()