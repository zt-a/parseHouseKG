# parseHouseKG

Парсер сайта [house.kg](https://www.house.kg/kupit) — собирает **только текстовые данные + URL-ы фотографий** (картинки не скачиваются).

## Возможности
- Обходит листинг `house.kg/kupit` (пагинация `?page=N`), дедуплицирует карточки
- Парсит детальные страницы `/details/<slug>` — вытаскивает все основные поля (дом/квартиры), коммуникации, безопасность, описание
- Извлекает **полный список URL фото** из галереи (CDN `cdn.house.kg`), без загрузки файлов
- Сохраняет всё в **один SQLite-файл** (`housekg.db`)
- Работает без Playwright (только requests + BeautifulSoup), SSR-страницы отдаются целиком
- Учитывает `robots.txt` (не трогаем `/api/`)

## Установка
```bash
cd /mnt/hdd/Projects/tools/parseHouseKG
pip install -r requirements.txt
```

## Запуск

Базовый (все категории купли, лимит 10 000):
```bash
python run.py --limit 10000
```

Только дома:
```bash
python run.py --category buy_house --limit 10000
```

Квартиры:
```bash
python run.py --category buy_apart --limit 10000
```

Указать путь к БД:
```bash
python run.py --limit 5000 --db /path/to/housekg.db
```

Ограничить страницами листинга (быстрый тест):
```bash
python run.py --limit 40 --max-pages 2
```

## Категории
- `buy_all` (по умолчанию) — `/kupit`
- `buy_house` — `/kupit-dom`
- `buy_apart` — `/kupit-kvartiru`
- `buy_land` — `/kupit-uchastok`
- `buy_room` — `/kupit-komnatu`
- `buy_commercial` — `/kupit-kommercheskaia-nedvijimost`
- `buy_dacha` — `/kupit-dachu`
- `buy_parking` — `/kupit-parking-garaj`

## Структура БД (SQLite)

Таблица `properties` (один файл). Ключевые поля:
- `url_slug` — уникальный ID объявления (из `/details/<slug>`) — PRIMARY KEY
- `detail_url` — полная ссылка
- `price_som`, `price_usd` — цена
- `price_m2_som`, `price_m2_usd` — цена за м²
- `address`, `city`, `district`, `region`, `town`
- `rooms`, `total_area`, `living_area`, `kitchen_area`, `land_area_sotka`
- `floor`, `floors_total`, `ceiling_height`, `year_built`, `condition`
- `documents`, `exchange`, `installment` (0/1), `mortgage` (0/1)
- `heating`, `gas`, `water`, `electricity`, `canalization`, `internet`, `furniture`, `flooring`, `toilet`, `security`
- `features_json` — массив фич ("сад", "хозпостройки", "кодовый замок", ...)
- `raw_params_json` — все пары dt/dd (для расширения)
- `badges_json` — бейджи ("Собственник", "Срочно", "Ниже рынка...")
- `seller_*` — данные продавца
- `photo_count`, `image_urls_json` — **только URL фото** (JSON-массив)
- `published_at`, `created_at_hk`, `updated_at_hk`
- `scraped_at` — UTC время парсинга

## Примечания
- Карточки на листинге дублируются в DOM — парсер дедуплицирует по ссылке
- Галерея в DOM даёт полный список фото (JSON-LD может содержать подмножество) — берём DOM
- Цены с символом `⃀` (U+20C0) нормализуются
- Поведение бережное: задержки 0.5–1.5с между запросами, ретраи при ошибках
- Запрещено ходить в `/api/` (robots.txt) — не используем

## Быстрый просмотр БД
```bash
sqlite3 housekg.db "SELECT count(*) FROM properties;"
sqlite3 housekg.db ".mode column" ".headers on" "SELECT url_slug, price_som, total_area, rooms, address FROM properties LIMIT 5;"
sqlite3 housekg.db "SELECT json_array_length(image_urls_json) as n, image_urls_json FROM properties LIMIT 1;"
```
