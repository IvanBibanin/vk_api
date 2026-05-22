# vk_api

Небольшой Python-пакет для работы с VK Ads API из Jupyter Notebook:

- выгрузка статистики VK Ads в `pandas.DataFrame`;
- раскрытие вложенного JSON через `pd.json_normalize`;
- выгрузка списка кампаний/планов с постраничной пагинацией `limit` / `offset`;
- сохранение данных в Excel;
- загрузка DataFrame в PostgreSQL через отдельный пакет `to_postgresql`.

## Установка

В Jupyter Notebook:

```python
!pip install git+https://github.com/IvanBibanin/vk_api.git
!pip install git+https://github.com/IvanBibanin/to_postgresql.git
```

Если пакет уже установлен и нужно подтянуть свежую версию из GitHub:

```python
!pip uninstall -y ivan-vk-api
!pip install --no-cache-dir --force-reinstall git+https://github.com/IvanBibanin/vk_api.git@main
!pip install --no-cache-dir --force-reinstall git+https://github.com/IvanBibanin/to_postgresql.git@main
```

После переустановки лучше перезапустить kernel Jupyter.

## Импорт

```python
from vk_api import Vk
from to_postgresql import ToPostgreSQL
```

Для обратной совместимости также работает старое имя:

```python
from to_postgresql import to_postgresql
```

## Быстрый старт

```python
from vk_api import Vk

vk = Vk(token="ВАШ_VK_ADS_TOKEN")
```

Не храните токены и пароли в репозитории. Для рабочих ноутбуков лучше брать их из переменных окружения:

```python
import os

vk = Vk(token=os.getenv("VK_ADS_TOKEN"))
```

## Получить список кампаний

Метод `get_campaigns_name()` получает все страницы `/api/v2/ad_plans.json` через `limit` и `offset`.

```python
df_campane_name = vk.get_campaigns_name(limit=100)

df_campane_name.head()
```

Пример колонок:

```text
event_limit
id
name
uniq_shows_limit
uniq_shows_period
```

Если в API больше объектов, чем помещается в один ответ, метод сам сделает несколько запросов:

```text
limit=100, offset=0
limit=100, offset=100
limit=100, offset=200
...
```

## Получить статистику кампаний

Метод `get_campaigns()` обращается к:

```text
https://ads.vk.com/api/v2/statistics/{type_object}/day.json
```

Базовый пример:

```python
df_campane = vk.get_campaigns(
    type_object="ad_plans",
    date_from="2026-05-18",
    date_to="2026-05-18"
)

df_campane.head()
```

Если нужны только отдельные метрики, передайте список в `metriks`:

```python
metriks = [
    "id",
    "date",
    "base_shows",
    "base_clicks",
    "base_goals",
    "base_spent",
    "base_vk_goals",
    "social_network_vk_subscribe",
    "social_network_vk_join",
    "social_network_ok_join",
    "social_network_dzen_join",
    "social_network_vk_message",
    "social_network_ok_message",
]

df_campane = vk.get_campaigns(
    type_object="ad_plans",
    metriks=metriks,
    date_from="2026-05-18",
    date_to="2026-05-18"
)
```

Если указать колонку, которой нет в DataFrame, метод выведет список отсутствующих колонок и покажет все доступные колонки.

## Посмотреть все доступные колонки

```python
df_campane = vk.get_campaigns(
    type_object="ad_plans",
    date_from="2026-05-18",
    date_to="2026-05-18"
)

df_campane.columns.tolist()
```

Или по одной колонке в строку:

```python
for column in df_campane.columns:
    print(column)
```

В Jupyter можно отключить сокращение колонок:

```python
import pandas as pd

pd.set_option("display.max_columns", None)
```

## Как раскрывается JSON

В ответе VK Ads статистика лежит во вложенной структуре:

```python
{
    "items": [
        {
            "id": 13412092,
            "total": {...},
            "rows": [
                {
                    "date": "2026-05-18",
                    "base": {
                        "shows": 8738,
                        "clicks": 17,
                        "vk": {
                            "goals": 4,
                            "cpa": "125"
                        }
                    }
                }
            ]
        }
    ]
}
```

Внутри класса используется:

```python
pd.json_normalize(
    data["items"],
    record_path="rows",
    meta=["id"],
    sep="_"
)
```

Поэтому вложенные поля превращаются в плоские колонки:

```text
base_shows
base_clicks
base_vk_goals
base_vk_cpa
```

## Сохранить DataFrame в Excel

```python
df_campane.to_excel("campaigns_data.xlsx", index=False)
```

В конкретную папку:

```python
df_campane.to_excel("/Users/ivan/Downloads/campaigns_data.xlsx", index=False)
```

Если Excel-запись не работает, установите `openpyxl`:

```python
!pip install openpyxl
```

## Подключение к PostgreSQL

```python
from to_postgresql import ToPostgreSQL

to_pg = ToPostgreSQL(
    port=6543,
    host="your-postgres-host",
    user="your-user",
    password="your-password",
    database="postgres"
)
```

Можно использовать старое имя класса:

```python
from to_postgresql import to_postgresql

to_pg = to_postgresql(
    port=6543,
    host="your-postgres-host",
    user="your-user",
    password="your-password",
    database="postgres"
)
```

## Создать таблицы

Таблица со статистикой:

```python
to_pg.create_table(data=df_campane, table_name="ВК_МИШИДО", schema="kg_globaltreid")
```

Таблица со справочником кампаний:

```python
to_pg.create_table(data=df_campane_name, table_name="ВК_МИШИДО_KM", schema="kg_globaltreid")
```

Важно: `create_table()` использует `CREATE TABLE IF NOT EXISTS`. Если таблица уже есть, PostgreSQL не добавит новые колонки автоматически.

Если структура DataFrame изменилась, проще пересоздать таблицу:

```python
to_pg.sql_query('DROP TABLE IF EXISTS "kg_globaltreid"."ВК_МИШИДО_KM"')
to_pg.create_table(data=df_campane_name, table_name="ВК_МИШИДО_KM", schema="kg_globaltreid")
```

## Загрузить данные в PostgreSQL

```python
to_pg.insert_into_table(data=df_campane, table_name="ВК_МИШИДО", schema="kg_globaltreid")
to_pg.insert_into_table(data=df_campane_name, table_name="ВК_МИШИДО_KM", schema="kg_globaltreid")
```

## Повторная загрузка без дублей

### Статистика: удалить период по date

Перед повторной вставкой статистики удалите старые строки за тот же период:

```python
to_pg.sql_query(
    'DELETE FROM "kg_globaltreid"."ВК_МИШИДО" '
    'WHERE "date" BETWEEN DATE \'2026-05-18\' AND DATE \'2026-05-18\''
)

to_pg.insert_into_table(data=df_campane, table_name="ВК_МИШИДО", schema="kg_globaltreid")
```

В PostgreSQL даты пишутся в одинарных кавычках:

```sql
DATE '2026-05-18'
```

Двойные кавычки используются для имен схем, таблиц и колонок:

```sql
"kg_globaltreid"."ВК_МИШИДО"
```

### Справочник кампаний: очистить всю таблицу

Для справочника кампаний обычно проще полностью очистить таблицу и вставить свежий список:

```python
to_pg.sql_query('DELETE FROM "kg_globaltreid"."ВК_МИШИДО_KM"')
to_pg.insert_into_table(data=df_campane_name, table_name="ВК_МИШИДО_KM", schema="kg_globaltreid")
```

### Справочник кампаний: удалить только текущие id

Если нужно удалить только кампании, которые есть в текущем DataFrame:

```python
ids = df_campane_name["id"].dropna().unique().tolist()
ids_sql = ", ".join(f"'{int(x)}'" for x in ids)

to_pg.sql_query(
    f'DELETE FROM "kg_globaltreid"."ВК_МИШИДО_KM" '
    f'WHERE "id" IN ({ids_sql})'
)

to_pg.insert_into_table(data=df_campane_name, table_name="ВК_МИШИДО_KM", schema="kg_globaltreid")
```

В текущей версии `ToPostgreSQL` все колонки, кроме `date` и `Дата`, создаются как `TEXT`, поэтому значения `id` в SQL нужно сравнивать как строки:

```sql
WHERE "id" IN ('4006492', '4036452')
```

А не как числа:

```sql
WHERE "id" IN (4006492, 4036452)
```

## Полный пример для Jupyter

```python
from vk_api import Vk
from to_postgresql import ToPostgreSQL


vk = Vk(token="ВАШ_VK_ADS_TOKEN")

date_from = "2026-05-18"
date_to = "2026-05-18"

metriks = [
    "id",
    "date",
    "base_shows",
    "base_clicks",
    "base_goals",
    "base_spent",
    "base_vk_goals",
    "social_network_vk_subscribe",
    "social_network_vk_join",
    "social_network_ok_join",
    "social_network_dzen_join",
    "social_network_vk_message",
    "social_network_ok_message",
]

df_campane = vk.get_campaigns(
    type_object="ad_plans",
    metriks=metriks,
    date_from=date_from,
    date_to=date_to
)

df_campane_name = vk.get_campaigns_name(limit=100)

to_pg = ToPostgreSQL(
    port=6543,
    host="your-postgres-host",
    user="your-user",
    password="your-password",
    database="postgres"
)

to_pg.create_table(data=df_campane, table_name="ВК_МИШИДО", schema="kg_globaltreid")
to_pg.create_table(data=df_campane_name, table_name="ВК_МИШИДО_KM", schema="kg_globaltreid")

to_pg.sql_query(
    f'DELETE FROM "kg_globaltreid"."ВК_МИШИДО" '
    f"WHERE \"date\" BETWEEN DATE '{date_from}' AND DATE '{date_to}'"
)

to_pg.insert_into_table(data=df_campane, table_name="ВК_МИШИДО", schema="kg_globaltreid")

to_pg.sql_query('DELETE FROM "kg_globaltreid"."ВК_МИШИДО_KM"')
to_pg.insert_into_table(data=df_campane_name, table_name="ВК_МИШИДО_KM", schema="kg_globaltreid")
```

## Частые ошибки

### `NameError: name 'sqlalchemy' is not defined`

Скорее всего, в Jupyter загружена старая установленная версия пакета.

Переустановите пакет и перезапустите kernel:

```python
!pip uninstall -y ivan-vk-api
!pip install --no-cache-dir --force-reinstall git+https://github.com/IvanBibanin/vk_api.git@main
!pip install --no-cache-dir --force-reinstall git+https://github.com/IvanBibanin/to_postgresql.git@main
```

### `ImportError: cannot import name 'ToPostgreSQL'`

Обновите пакет. В актуальной версии работают оба импорта:

```python
from to_postgresql import ToPostgreSQL
from to_postgresql import to_postgresql
```

### `column "2026-05-18" does not exist`

В SQL дата была написана в двойных кавычках:

```sql
"2026-05-18"
```

Нужно писать в одинарных:

```sql
DATE '2026-05-18'
```

### `operator does not exist: text = integer`

Колонка `"id"` создана как `TEXT`, а сравнение идет с числами.

Нужно так:

```sql
WHERE "id" IN ('4006492', '4036452')
```

Или очистить весь справочник:

```python
to_pg.sql_query('DELETE FROM "kg_globaltreid"."ВК_МИШИДО_KM"')
```

### `column ... does not exist`

Таблица уже была создана раньше с другим набором колонок. `CREATE TABLE IF NOT EXISTS` не меняет существующую таблицу.

Решение: пересоздать таблицу или добавить недостающие колонки через `ALTER TABLE`.

```python
to_pg.sql_query('DROP TABLE IF EXISTS "kg_globaltreid"."ВК_МИШИДО_KM"')
to_pg.create_table(data=df_campane_name, table_name="ВК_МИШИДО_KM", schema="kg_globaltreid")
```

## Ограничения текущей версии

- `ToPostgreSQL` создает `DATE` только для колонок `date` и `Дата`.
- Остальные колонки создаются как `TEXT`.
- `create_table()` не добавляет новые колонки в уже существующую таблицу.
- `insert_into_table()` делает обычный `INSERT`, без `UPSERT`.
- Для повторной загрузки нужно заранее удалить старые строки.

## Структура репозитория

```text
vk_api.py          # класс Vk для VK Ads API
setup.py           # установка пакета из GitHub
README.md          # документация и примеры
```
