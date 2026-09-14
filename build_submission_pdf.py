from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, Preformatted, SimpleDocTemplate

pdfmetrics.registerFont(TTFont("NotoSans", "/usr/share/fonts/noto/NotoSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("NotoSans-Bold", "/usr/share/fonts/noto/NotoSans-Bold.ttf"))
styles = getSampleStyleSheet()
base = ParagraphStyle("base", parent=styles["BodyText"], fontName="NotoSans", fontSize=9.4, leading=12, spaceAfter=6)
h1 = ParagraphStyle("h1", parent=base, fontName="NotoSans-Bold", fontSize=16, leading=19, spaceAfter=12)
h2 = ParagraphStyle("h2", parent=base, fontName="NotoSans-Bold", fontSize=13, leading=16, spaceBefore=10, spaceAfter=7)
h3 = ParagraphStyle("h3", parent=base, fontName="NotoSans-Bold", fontSize=10.5, leading=13, spaceBefore=6, spaceAfter=3)
code = ParagraphStyle("code", parent=base, fontName="NotoSans", backColor=colors.HexColor("#f2f2f2"), leftIndent=5, rightIndent=5, spaceBefore=4, spaceAfter=4)
P = lambda text, style=base: Paragraph(text, style)

story = [
    P("Тестовое задание — аналитик данных DaData", h1),
    P("Задание 1. Справочник «организация — официальный сайт»", h2),
]
sections = [
("Цель и принципы", "Нужно дополнить сервис «Организация по ИНН» доменом официального сайта. Для такого поля существенно важнее точность, чем полнота: ошибочно привязать сайт одноимённой организации, франшизы или холдинга хуже, чем вернуть пустое значение. Поэтому домен — сущность с доказательствами и уровнем уверенности, а не необратимое текстовое поле."),
("Сбор данных", "Первый слой — карточка юридического лица из DaData/официальных источников: ИНН, полное и сокращённое наименование, ОГРН, адрес, руководитель, статус и, если поставщик его отдаёт, web-домен. Он решает entity resolution: поиск ведётся не только по бренду, но и по точной юридической сущности.\n\nВторой слой — поиск кандидатов. Формирую несколько запросов: точное название + ИНН, название + «официальный сайт», бренд + адрес. Из Web Search беру URL, title, snippet, дату/регион, если они доступны. Дополнительно можно использовать официальный реестр, страницы контрагентов, реквизиты на сайтах и открытые API. URL нормализую до hostname: убираю www, параметры, дубли и очевидно нецелевые платформы — поисковики, соцсети, карты и агрегаторы.\n\nДля масштабного наполнения применил бы двухконтурную схему. Высокоуверенные записи создаются автоматически, спорные попадают в review-очередь с собранными доказательствами. Это даёт контролируемый старт без ручной проверки всего реестра."),
("Оценка качества", "Кандидат получает признаки: точное совпадение названия/ИНН в тексте сайта, совпадение адреса/ОГРН, наличие разделов «контакты» и реквизитов, совпадение бренда в title, независимые подтверждения несколькими источниками, история домена. LLM используется как рецензент доказательств, но не как источник истины: ей передаётся ограниченный пакет evidence и предписывается выбрать домен или null.\n\nРешение проходит детерминированную проверку: выбранный домен обязан быть среди найденных URL, иметь supporting URL из evidence, не попадать в blacklist платформ и иметь medium/high confidence. При конфликте или недостатке доказательств возвращается null.\n\nКачество измеряю на размеченной выборке: precision принятых доменов, coverage, доля null, доля спорных записей, расхождения при повторной проверке и latency. Для приёмки отдельно проверю длинный хвост: одинаковые названия, группы компаний, ликвидированные юрлица, переезды и домены с редиректами."),
("Актуализация", "Для каждой записи храню ИНН, fingerprint исходной карточки, домен, confidence, evidence URLs, timestamps и результат ручной проверки. Переобогащение запускается по TTL; ускоренно — при изменении названия/адреса/статуса, падении сайта, сигнале от пользователя или низкой уверенности. Изменение домена не перезаписывает старый результат молча: новая версия получает собственные evidence и может требовать review."),
("Открытые вопросы и ограничения", "Не у каждой организации есть индексируемый сайт. Есть холдинги, торговые марки, филиалы, сайты на конструкторах и устаревшие snippets. Юридическое имя может не совпадать с брендом. Эти случаи — причина предпочесть null ложному совпадению. Также нужны политика хранения персональных данных, лимиты и условия внешних API, мониторинг стоимости поиска/LLM и feedback от пользователей."),
]
for title, text in sections:
    story.append(P(title, h3))
    for part in text.split("\n\n"):
        story.append(P(part))
story += [
    PageBreak(),
    P("Задание 2. Python агентный пайплайн", h2),
    P("Репозиторий: https://github.com/bigidulka/dadata-inn-site-finder"),
    P("Контракт", h3),
    P("Вход: ИНН из 10 или 12 цифр. Выход всегда имеет минимальный JSON-контракт:"),
    Preformatted('{"domain": "dadata.ru"}\n# или\n{"domain": null}', code),
    P("Архитектура", h3),
]
for item in [
    "1. DaDataClient получает карточку организации по ИНН.",
    "2. BraveSearchClient ищет кандидаты запросом из полного имени, ИНН и «официальный сайт».",
    "3. Нормализатор приводит URL к hostname и фильтрует поисковые/социальные/агрегаторные домены.",
    "4. OpenAICompatibleAssessor получает строго ограниченную карточку сущности и evidence, возвращает structured JSON: domain, confidence, rationale, supporting_urls.",
    "5. SiteFinder принимает ответ только после детерминированной валидации кандидата и цитаты; в остальных случаях возвращает null.",
]:
    story.append(P(item))
story += [
    P("Агенты разделены по ответственности: внешние API собирают факты, LLM сопоставляет доказательства, код контролирует инварианты контракта. Ключи передаются только через переменные окружения и не логируются."),
    P("Инструменты и проверка", h3),
    P("Использованы Python 3.11+, requests, DaData API, Brave Search API и OpenAI-compatible Chat Completions API. Провайдер и модель LLM конфигурируемы, поэтому можно выбрать доступный API с пробным лимитом из перечня задания. Проект покрыт четырьмя pytest-тестами с HTTP-фейками: пример задания 7721581040 → dadata.ru, галлюцинация LLM, запрещённый/низкоуверенный домен и валидация ИНН/URL. Локальный прогон: 4 passed."),
    P("Для настоящего запуска задаются DADATA_API_KEY, BRAVE_SEARCH_API_KEY, LLM_API_KEY; затем dadata-site-finder 7721581040 делает реальный поиск и выдаёт итоговый JSON. Реальные ключи не включались в репозиторий и не подменялись фиктивными результатами."),
]
out = Path("docs/dadata_submission.pdf")
SimpleDocTemplate(str(out), pagesize=A4, rightMargin=16*mm, leftMargin=16*mm, topMargin=15*mm, bottomMargin=15*mm, title="Тестовое задание — DaData").build(story)
print(out, out.stat().st_size)
