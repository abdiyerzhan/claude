# JupyterHub в Docker Compose с паролями пользователей

Готовый стенд JupyterHub, где каждый пользователь заходит под своим системным
Linux-логином и паролем (аутентификация через PAM), а домашние и общая папки
монтируются с хоста, так что данные не теряются при пересоздании контейнера.

## Состав

- `docker-compose.yml` — описание сервиса `jupyterhub` и томов
- `Dockerfile` — образ на базе `jupyterhub/jupyterhub`, ставит JupyterLab, стек для дата-сайентистов и создаёт пользователей
- `requirements.txt` — Python-пакеты для дата-сайенса (pandas, numpy, scikit-learn и др.)
- `check_packages.py` — смоук-тест на этапе сборки: проверяет, что все пакеты из `requirements.txt` реально импортируются
- `users.txt` — список пользователей в формате `username:password`
- `create_users.sh` — создаёт системных пользователей и задаёт пароли (выполняется при сборке образа)
- `entrypoint.sh` — при старте контейнера чинит права на примонтированные с хоста папки, кладёт стартовый ноутбук новым пользователям
- `jupyterhub_config.py` — конфигурация хаба (аутентификатор, спавнер, БД)
- `templates/welcome.ipynb` — стартовый ноутбук с примерами pandas/matplotlib/seaborn/sklearn

## Стек для дата-сайентистов

В образ уже включены (см. `requirements.txt`):

- **Данные**: numpy, pandas, scipy, polars, pyarrow, openpyxl
- **Визуализация**: matplotlib, seaborn, plotly
- **ML**: scikit-learn, statsmodels, xgboost, lightgbm
- **Базы данных**: oracledb
- **Прочее**: requests, tqdm, python-dotenv

Чтобы добавить/убрать пакеты, отредактируйте `requirements.txt` и
пересоберите образ: `docker compose up -d --build`.

> Ставьте новые Python-пакеты через `requirements.txt` и пересборку образа,
> а не через `pip install --user` из ноутбука. У JupyterHub-сервера
> пользовательский `site-packages` может не подхватываться сразу — пакет
> ставится, но `import` не находит его до перезапуска ядра, а иногда и после.
> Через `requirements.txt` пакет доступен всем пользователям сразу после
> старта контейнера.

Сразу после установки зависимостей `Dockerfile` запускает
`check_packages.py`, который импортирует каждый пакет из списка. Если
пакет не установился или не импортируется — `docker compose build`
упадёт с понятной ошибкой прямо на этом шаге, а не всплывёт позже как
`ModuleNotFoundError` в чьей-то тетрадке.

### Подключение к Oracle (`oracledb`)

Пакет `oracledb` по умолчанию работает в **thin-режиме** — чистый Python,
Oracle Instant Client не нужен. Достаточно строки подключения:

```python
import oracledb

conn = oracledb.connect(
    user="myuser",
    password="mypassword",
    dsn="myhost.example.com:1521/mydb_service",  # host:port/service_name
)
cur = conn.cursor()
cur.execute("SELECT * FROM dual")
print(cur.fetchall())
```

Thin-режим подходит для Oracle Database 12.1 и новее. Если нужен
thick-режим (старые версии БД, TNS-алиасы, advanced queuing) — потребуется
отдельно установить Oracle Instant Client в образ и вызвать
`oracledb.init_oracle_client()`; в базовой поставке этого стенда он не
включён, чтобы не раздувать образ без необходимости.

## Стартовый ноутбук

При первом запуске в рабочую папку каждого пользователя (`/home/<user>/work`)
копируется `templates/welcome.ipynb` с примерами использования pandas,
matplotlib, seaborn и scikit-learn. Файл копируется только если его там ещё
нет, поэтому существующая работа пользователя не перезаписывается при
перезапуске контейнера.

## Быстрый старт

1. Отредактируйте `users.txt` — задайте своих пользователей и пароли:

   ```
   admin:supersecret
   alice:alicepass
   bob:bobpass
   ```

   Для каждого пользователя в `docker-compose.yml` нужен свой volume для
   домашней папки (`./notebooks/<user>:/home/<user>`) — добавьте/удалите
   строки под новых пользователей.

2. Соберите и запустите:

   ```bash
   docker compose up -d --build
   ```

3. Откройте `http://localhost:8000` и войдите под одним из пользователей
   из `users.txt`.

## Монтирование папок

- `./notebooks/<user>` (хост) → `/home/<user>` (контейнер) — персональная
  домашняя папка каждого пользователя, ноутбуки сохраняются на хосте.
- `./shared` (хост) → `/srv/shared` (контейнер) — общая папка, доступна на
  чтение/запись всем пользователям (права `1777`).
- `jupyterhub_data` (именованный volume) → `/srv/jupyterhub/data` — база
  данных хаба и cookie secret, чтобы состояние хаба переживало пересоздание
  контейнера.
- `./jupyterhub_config.py` монтируется в контейнер `:ro`, поэтому конфиг
  можно менять и просто перезапускать контейнер (`docker compose restart`)
  без пересборки образа.

## Добавление нового пользователя

1. Добавьте строку `username:password` в `users.txt`.
2. Добавьте volume `./notebooks/username:/home/username` в `docker-compose.yml`.
3. Пересоберите образ: `docker compose up -d --build` (пользователи Linux
   создаются на этапе сборки, поэтому нужен ребилд).

## Важно про безопасность

- `users.txt` содержит пароли в открытом виде — не коммитьте реальные
  пароли в репозиторий, используйте `.gitignore` или secrets-механизм
  Docker Swarm/Compose для продакшена.
- Аутентификация через PAM создаёт настоящих Linux-пользователей внутри
  контейнера — подходит для небольших команд/учебных стендов; для
  продакшена с изоляцией по контейнерам на пользователя рассмотрите
  `DockerSpawner` вместо `LocalProcessSpawner`.
