# JupyterHub в Docker Compose с паролями пользователей

Готовый стенд JupyterHub: каждый пользователь заходит под своим системным
Linux-логином и паролем (аутентификация через PAM), домашние и общая папки
монтируются с хоста, доступ идёт по HTTPS через nginx, стек для
дата-сайентистов уже установлен, а поломки пакетов ловятся на этапе сборки.

## Состав

- `docker-compose.yml` — сервисы `jupyterhub` и `nginx`, тома
- `Dockerfile` — образ на базе `jupyterhub/jupyterhub`, ставит JupyterLab и стек для дата-сайентистов
- `requirements.txt` — Python-пакеты с зафиксированными диапазонами версий
- `check_packages.py` — смоук-тест на этапе сборки: проверяет, что все пакеты из `requirements.txt` реально импортируются
- `users.txt.example` — шаблон списка пользователей (`username:password`); реальный `users.txt` — вне git
- `create_users.sh` — создаёт/обновляет системных пользователей и пароли при **старте** контейнера
- `entrypoint.sh` — при старте создаёт пользователей, чинит права на примонтированные папки, кладёт стартовый ноутбук
- `jupyterhub_config.py` — конфигурация хаба (аутентификатор, спавнер, idle-culler, БД)
- `templates/welcome.ipynb` — стартовый ноутбук с примерами pandas/matplotlib/seaborn/sklearn
- `nginx/` — reverse-proxy: TLS-терминация, самоподписанный сертификат генерируется автоматически
- `.github/workflows/docker-build.yml` — CI: собирает образы и гоняет смоук-тест на каждый push/PR

## Быстрый старт

1. Скопируйте шаблон пользователей и задайте свои логины/пароли:

   ```bash
   cp users.txt.example users.txt
   ```

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

3. Откройте `https://localhost` и войдите под одним из пользователей из
   `users.txt`. Браузер покажет предупреждение о самоподписанном
   сертификате (см. раздел про HTTPS ниже) — это ожидаемо для локального
   стенда, подтвердите переход.

## HTTPS

Весь трафик идёт через сервис `nginx` (`nginx/`): порт 80 редиректит на
443, TLS терминируется в nginx, дальше запрос по внутренней docker-сети
идёт в `jupyterhub:8000` (наружу этот порт больше не публикуется — только
через nginx). Сертификат самоподписанный, генерируется автоматически при
первом старте (`nginx/entrypoint.sh`) и хранится в volume `nginx_certs`,
поэтому не пересоздаётся при каждом рестарте.

Для локального/внутреннего стенда самоподписанного сертификата достаточно.
Если нужен реальный домен без предупреждений браузера — замените
`nginx/entrypoint.sh` и `nginx/nginx.conf` на связку с Let's Encrypt
(certbot) или поставьте перед этим стендом Traefik/внешний балансировщик,
который сам управляет сертификатами.

## Стек для дата-сайентистов

В образ включены (см. `requirements.txt`, версии зафиксированы диапазонами):

- **Данные**: numpy, pandas, scipy, polars, pyarrow, openpyxl
- **Визуализация**: matplotlib, seaborn, plotly
- **ML**: scikit-learn, statsmodels, xgboost, lightgbm
- **Базы данных**: oracledb
- **Удобство работы**: jupyterlab-git, nbdime, ipywidgets, jupyterlab-lsp + python-lsp-server
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
пакет не установился или не импортируется — `docker build` упадёт с
понятной ошибкой прямо на этом шаге, а не всплывёт позже как
`ModuleNotFoundError` в чьей-то тетрадке. Тот же смоук-тест гоняется в CI
(`.github/workflows/docker-build.yml`) на каждый push и pull request.

### Работа с git из JupyterLab

- **jupyterlab-git** — вкладка Git прямо в интерфейсе (commit/push/pull),
  не нужно выходить в терминал.
- **nbdime** — человекочитаемый diff/merge для `.ipynb` включён системно
  (`git diff` по ноутбуку показывает изменения по ячейкам, а не простыню JSON).
- Перед первым коммитом пользователю нужно задать имя/почту:
  ```bash
  git config --global user.name "Имя"
  git config --global user.email "email@example.com"
  ```

### Подключение к Oracle (`oracledb`)

Пакет `oracledb` по умолчанию работает в **thin-режиме** — чистый Python,
Oracle Instant Client не нужен:

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

## Монтирование папок

- `./notebooks/<user>` (хост) → `/home/<user>` (контейнер) — персональная
  домашняя папка каждого пользователя, ноутбуки сохраняются на хосте.
- `./shared` (хост) → `/srv/shared` (контейнер) — общая папка, доступна на
  чтение/запись всем пользователям (права `1777`).
- `jupyterhub_data` (именованный volume) → `/srv/jupyterhub/data` — база
  данных хаба и cookie secret, чтобы состояние хаба переживало пересоздание
  контейнера.
- `nginx_certs` (именованный volume) → `/etc/nginx/certs` — TLS-сертификат
  nginx, переживает пересоздание контейнера.
- `./jupyterhub_config.py` и `./users.txt` монтируются `:ro` — конфиг и
  список пользователей можно менять и просто перезапускать контейнер
  (`docker compose restart jupyterhub`) без пересборки образа.

## Добавление нового пользователя

1. Добавьте строку `username:password` в `users.txt`.
2. Добавьте volume `./notebooks/username:/home/username` в `docker-compose.yml`.
3. Перезапустите контейнер — пересборка не нужна, пользователи создаются
   при старте:
   ```bash
   docker compose restart jupyterhub
   ```

## Автоочистка неактивных серверов (idle-culler)

`jupyterhub_config.py` регистрирует сервис `idle-culler`
(`jupyterhub-idle-culler`), который каждые 5 минут проверяет
пользовательские серверы и гасит те, что простаивают дольше часа
(`--timeout=3600 --cull-every=300`). Это защищает общий хост от
накопления памяти неактивными ядрами. Значения можно поменять прямо в
`jupyterhub_config.py`.

## Лимиты ресурсов

- **На весь контейнер `jupyterhub`**: `mem_limit: 4g` и `cpus: 2.0` в
  `docker-compose.yml` — реальный лимит на уровне Docker, защищает хост.
- **На отдельного пользователя**: `c.Spawner.mem_limit`/`cpu_limit` в
  `jupyterhub_config.py` заданы, но носят **информационный** характер —
  используемый здесь `LocalProcessSpawner` их не применяет принудительно
  (все пользовательские ноутбук-серверы делят общий лимит контейнера
  выше). Для реального ограничения ресурсов на пользователя нужен
  спавнер, который это умеет — `DockerSpawner` (свой контейнер на
  пользователя) или `SystemdSpawner` (cgroups через systemd). Это уже
  архитектурное изменение стенда, не конфигурационная правка.

## CI

`.github/workflows/docker-build.yml` на каждый push и pull request:
собирает образ `jupyterhub` (со смоук-тестом `check_packages.py` внутри),
собирает образ `nginx` и валидирует `docker-compose.yml`. Ломающиеся
зависимости или синтаксические ошибки конфигурации всплывают в CI, а не
после деплоя.

## Важно про безопасность

- `users.txt` содержит пароли в открытом виде и **не коммитится в git**
  (`.gitignore`) — в репозитории только шаблон `users.txt.example`. Для
  продакшена рассмотрите secrets-механизм Docker Swarm/Compose вместо
  файла с паролями.
- Пользователи создаются при **старте контейнера**, а не при сборке
  образа — пароли не оседают в слоях образа (`docker history`/`docker save`
  их не покажут).
- Аутентификация через PAM создаёт настоящих Linux-пользователей внутри
  контейнера — подходит для небольших команд/учебных стендов; для
  продакшена с изоляцией по контейнерам на пользователя рассмотрите
  `DockerSpawner` вместо `LocalProcessSpawner`.
- HTTPS включён по умолчанию (самоподписанный сертификат) — пароли не
  идут по сети в открытом виде.
