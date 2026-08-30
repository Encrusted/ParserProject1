import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import os
import re

baseUrl = "https://hh.ru"
authFile = "auth.json"
async def fetch_page_html(search_query: str, page: int = 0) -> str:
    """функция запускает браузер headless=False для отладочных целей. Браузер запускам с сохранением сессии
    для обхода всплывающих баннеров"""
    async with async_playwright() as p:
        if not os.path.exists(authFile):
            print(f"\n[{authFile} не найден], запускаем браузер для первой настройки, у нас 40 секунд")
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1376, "height": 768}
            )

            page_obj = await context.new_page()
            await page_obj.goto("https://hh.ru")
            await asyncio.sleep(40)
            await context.storage_state(path=authFile)
            print(f"Сессия успешно сохранена в {authFile}! Перезапустите скрипит")
            await browser.close()
            return ""


        print(f"Используем сохраненную сессию {authFile}")
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context(
            storage_state=authFile,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800})
        page_obj = await context.new_page()
        url = f"{baseUrl}?text={search_query}&page={page}"
        print(f"Открываем страницу: {url}")
        await page_obj.goto(url, wait_until="commit")
        await asyncio.sleep(5)
        await page_obj.screenshot(path="hh_screen.png")
        print("Скриншот страницы сохранен в файл 'hh_screen.png'")
        html = await page_obj.content()
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(html)
        await browser.close()
        return html
def parse_vacancies(html: str):
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    """на момент создания кода карточка имеет атрибут data-qa, так называется класс.
    возможно атрибут vacancy-cards нужно отредактировать"""
    vacancy_cards = soup.find_all("div", {"data-qa": "vacancy-serp__vacancy"})
    if not vacancy_cards:
        vacancy_cards = soup.find_all("article")
    if not vacancy_cards:
        vacancy_cards = soup.find_all("div", class_=lambda x: x and "vacancy-card" in x)
    print(f"Найдено карточек на стр: {len(vacancy_cards)}")
    parsed_data = []
    for card in vacancy_cards:
        try:
            title_tag = card.find("a", {"data-qa": "serp-item__title"}) or card.find("a",
                                                                                     class_=lambda x: x and "title" in x)
            if not title_tag or isinstance(title_tag, tuple) or not hasattr(title_tag, "text"):
                continue

            title = title_tag.text.strip()
            url = title_tag.get("href", "")
            hh_id = None
            match = re.search(r"/vacancy/(\d+)", url)
            if match:
                hh_id = match.group(1)
            salary_tag = (card.find("span", {"data-qa": "vacancy-salary"}) or
                          card.find("span", class_=lambda
                x: x and "salary" in x))
            salary_raw = "Не указана"
            if salary_tag and hasattr(salary_tag, "text") and not isinstance(salary_tag, tuple):
                salary_raw = salary_tag.text.strip()
            schedule_tag = (card.find("div", {"data-qa": "work-schedule-by-days-text"}) or
                            card.find("div",class_=lambda x: x and "schedule" in x))
            schedule = "Не указан"
            if schedule_tag and hasattr(schedule_tag, "text") and not isinstance(schedule_tag, tuple):
                schedule = schedule_tag.text.strip()
            parsed_data.append({
                    "hh_id": hh_id,
                    "title": title,
                    "url": url,
                    "salary_raw": salary_raw,
                    "schedule": schedule,
                    "skills": []
                })
        except Exception as e:
            print(f"Ошибка при разборе карточки: {e}")
            continue
    return parsed_data
async def main():

    html = await fetch_page_html(search_query="Python", page =0)
    vacancies = parse_vacancies(html)
    print("\n--- test results ---")
    for vac in vacancies: #первые три, значение можно менять опытным путем
        print(f"ID: {vac['hh_id']} || {vac['title']} || $$: {vac['salary_raw']} || График: {vac['schedule']}"
              f"|| url: {vac['url']}")
if __name__ == "__main__":
    asyncio.run(main())




