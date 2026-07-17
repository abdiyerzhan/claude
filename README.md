# JupyterHub в Docker Compose с паролями пользователей

Готовый стенд JupyterHub, где каждый пользователь заходит под своим системным
Linux-логином и паролем (аутентификация через PAM), а домашние и общая папки
монтируются с хоста, так что данные не теряются при пересоздании контейнера.

## Состав

- `docker-compose.yml` — описание сервиса `jupyterhub` и томов
- `Dockerfile` — образ на базе `jupyterhub/jupyterhub`, ставит JupyterLab, стек для дата-сайентистов и создаёт пользователей
- `requirements.txt` — Python-пакеты для дата-сайенса (pandas, numpy, scikit-learn и др.)
- `users.txt` — список пользователей в формате `username:password`
- `create_users.sh` — создаёт системных пользователей и задаёт пароли (выполняется при сборке образа)
- `entrypoint.sh` — при старте контейнера чинит права на примонтированные с хоста папки
- `jupyterhub_config.py` — конфигурация хаба (аутентификатор, спавнер, БД)

## Стек для дата-сайентистов

В образ уже включены (см. `requirements.txt`):

- **Данные**: numpy, pandas, scipy, polars, pyarrow, openpyxl
- **Визуализация**: matplotlib, seaborn, plotly
- **ML**: scikit-learn, statsmodels, xgboost, lightgbm
- **Прочее**: requests, tqdm, python-dotenv

Чтобы добавить/убрать пакеты, отредактируйте `requirements.txt` и
пересоберите образ: `docker compose up -d --build`.

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
