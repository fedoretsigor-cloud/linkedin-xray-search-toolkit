# LinkedIn X-Ray Search Toolkit

Небольшой переносимый проект для поиска IT-профилей через X-Ray Search без прямого парсинга LinkedIn.

## Что внутри

- генератор Google X-Ray запросов под LinkedIn;
- поиск через альтернативный search API;
- сохранение результатов в CSV;
- шаблон конфигурации через `.env`;
- понятная структура проекта под GitHub;
- инструкция, где в Google Cloud искать уже созданные ключи и ID.

## Структура

- `src/xray_search.py` - CLI-скрипт для генерации запросов
- `src/google_xray_to_csv.py` - поиск через SerpApi или Brave Search и сохранение в CSV
- `requirements.txt` - зависимости проекта
- `.env.example` - шаблон переменных окружения
- `.gitignore` - исключение секретов и служебных файлов
- `README.md` - инструкция по запуску и Google Cloud

## Быстрый старт

1. Убедись, что установлен Python 3.11+.
2. Создай виртуальное окружение:

```powershell
python -m venv .venv
```

3. Установи зависимости:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

4. Скопируй `.env.example` в `.env`.
5. Заполни переменные.
6. Запусти генератор X-Ray запроса:

```powershell
.\.venv\Scripts\python.exe .\src\xray_search.py --title "python developer" --skill django --skill fastapi --location germany
```

7. Запусти поиск и сохрани CSV:

```powershell
.\.venv\Scripts\python.exe .\src\google_xray_to_csv.py --title "python developer" --skill django --location germany --output .\output\linkedin_profiles.csv
```

## Как перенести на другой компьютер

1. Клонируй репозиторий.
2. Создай локальный `.env` на основе `.env.example`.
3. Создай виртуальное окружение:

```powershell
python -m venv .venv
```

4. Установи зависимости:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

5. Вставь свой `SERPAPI_API_KEY` в `.env`.
6. Запускай те же команды поиска.

Секреты и результаты поиска в GitHub не хранятся:

- `.env` не коммитится
- `output/` не коммитится
- `.venv/` не коммитится

## Как загрузить в GitHub

После инициализации локального git-репозитория типовой набор команд такой:

```powershell
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

## Пример результата

Скрипт `xray_search.py` собирает запросы вроде:

```text
site:linkedin.com/in/ ("python developer" OR "software engineer") ("django" OR "fastapi") ("germany")
```

Скрипт `google_xray_to_csv.py`:

- собирает X-Ray запрос;
- отправляет его в выбранный search API;
- вытаскивает найденные результаты;
- удаляет дубли по ссылке;
- сохраняет всё в CSV.

## Где в Google Cloud искать свои ключи и ID

Ниже актуальный путь по официальной документации Google Cloud.

### 1. API key

Открой страницу Credentials:

[Google Cloud Console - Credentials](https://console.cloud.google.com/apis/credentials)

Там обычно лежат:

- `API keys`
- `OAuth 2.0 Client IDs`
- `Service Accounts`

Если ключ уже создавался, ты увидишь его по имени. При открытии ключа можно проверить:

- сам ключ;
- `Key ID` или внутренний идентификатор;
- ограничения по API;
- ограничения по IP или referrer.

### 2. OAuth Client ID

На той же странице `Credentials` ищи блок `OAuth 2.0 Client IDs`.

Там можно увидеть:

- `Client ID`
- `Client secret`
- тип приложения

### 3. Service Account key

Если ты создавал JSON-ключ сервисного аккаунта, путь такой:

[Google Cloud Console - Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)

Дальше:

1. Выбери проект.
2. Открой нужный service account.
3. Перейди во вкладку `Keys`.

Важно: Google обычно не показывает скачанный private key повторно после создания. Можно увидеть, что ключ существует, но сам JSON-файл заново не раскрывается. Если файл потерян, обычно создают новый ключ и старый отзывают.

### 4. Как понять, что за "ID-шник" ты сохранил

Обычно путают несколько сущностей:

- `Project ID` - идентификатор проекта Google Cloud
- `Project Number` - числовой ID проекта
- `API Key` - строка ключа для запросов
- `Key ID` - внутренний ID ключа
- `OAuth Client ID` - длинный идентификатор клиента OAuth
- `Service Account email` - адрес сервисного аккаунта

Если принесешь сюда строку без секрета, я помогу быстро определить, что это именно было.

## Что лучше хранить в GitHub

Можно хранить:

- исходный код;
- `README.md`;
- `.env.example`;
- инструкции;
- шаблоны запросов.

Нельзя хранить:

- `.env`;
- реальные API keys;
- JSON-ключи сервисных аккаунтов;
- client secrets.

## Рекомендуемый workflow

1. Создать отдельный Google Cloud project именно под этот инструмент.
2. Включить только нужные API.
3. Хранить секреты в `.env`.
4. Держать код в GitHub.
5. На новом компьютере клонировать репозиторий и заново подставлять локальные секреты.

## Если хочешь подключить Google API позже

Для следующего шага нам обычно нужны:

- `GOOGLE_CLOUD_PROJECT_ID`
- `GOOGLE_API_KEY`
- иногда `GOOGLE_CSE_ID`, если будем использовать Programmable Search Engine

## Почему мы уходим от Google Custom Search JSON API

По официальной документации Google, `Custom Search JSON API` закрыт для новых клиентов.

- [Custom Search JSON API overview](https://developers.google.com/custom-search/v1/overview)

Поэтому для новых проектов практичнее сразу использовать альтернативного провайдера.

## Рекомендуемый провайдер для этой задачи

Для X-Ray поиска по LinkedIn лучше всего подходит `SerpApi`, потому что он работает с результатами Google и официально поддерживает обычный поисковый запрос через параметр `q`, включая операторы вроде `site:`:

- [SerpApi Google Search API](https://serpapi.com/search-api)
- [SerpApi pricing](https://serpapi.com/pricing)

Альтернатива: `Brave Search API`

- [Brave Search API](https://brave.com/search/api/)
- [Brave Search API pricing](https://api-dashboard.search.brave.com/documentation/pricing)

## Какой провайдер выбрать

### `SerpApi`

- лучше подходит именно для Google X-Ray логики;
- есть бесплатный тариф;
- результаты ближе к обычному Google поиску.

### `Brave Search`

- может быть дешевле на объеме;
- независимый индекс;
- результаты могут заметнее отличаться от Google.

## Что нужно для запуска через SerpApi

Нужна одна переменная:

- `SERPAPI_API_KEY`

Регистрация и ключ:

- [SerpApi](https://serpapi.com/)

Заполни `.env` так:

```dotenv
SEARCH_PROVIDER=serpapi
SEARCH_RESULTS_PER_QUERY=10
SERPAPI_API_KEY=your_serpapi_key
```

## Что нужно для запуска через Brave Search

Нужна одна переменная:

- `BRAVE_SEARCH_API_KEY`

Регистрация и ключ:

- [Brave Search API](https://brave.com/search/api/)

## Пример `.env`

```dotenv
SEARCH_PROVIDER=serpapi
SEARCH_RESULTS_PER_QUERY=10
SERPAPI_API_KEY=your_serpapi_key
```

## Пример CSV-экспорта

После запуска `google_xray_to_csv.py` появится файл вроде:

- `output/linkedin_profiles.csv`

В нем будут поля:

- `query`
- `name`
- `headline`
- `title`
- `link`
- `snippet`
- `display_link`
- `source`

## Массовый поиск за один запуск

Можно передавать несколько значений через повторяющиеся флаги:

```powershell
.\.venv\Scripts\python.exe .\src\google_xray_to_csv.py `
  --title "python developer" `
  --title "backend developer" `
  --skill django `
  --skill fastapi `
  --location germany `
  --location poland `
  --output .\output\batch_profiles.csv
```

Скрипт переберет комбинации запросов, соберет результаты и удалит дубли по профилю.

Также можно использовать текстовые файлы:

- `--titles-file`
- `--skills-file`
- `--locations-file`

Пример файла:

```text
python developer
backend developer
software engineer
```

## Полезные официальные ссылки

- [Manage API keys](https://cloud.google.com/docs/authentication/api-keys)
- [List and get service account keys](https://cloud.google.com/iam/docs/keys-list-get)
