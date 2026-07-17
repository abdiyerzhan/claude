FROM jupyterhub/jupyterhub:4

# Индекс pip настраиваемый — если соединение до files.pythonhosted.org
# медленное/нестабильное (типично для некоторых регионов), можно подставить
# более быстрое зеркало через --build-arg PIP_INDEX_URL=... (см. README).
ARG PIP_INDEX_URL=https://pypi.org/simple

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-pip \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /srv/jupyterhub/requirements.txt
# --retries/--timeout — устойчивость к медленному/нестабильному соединению
# при скачивании большого списка зависимостей (частая причина "No matching
# distribution found"/ReadTimeoutError для реально существующего пакета —
# это не конфликт версий, а сеть).
RUN python3 -m pip install --no-cache-dir \
        --index-url "$PIP_INDEX_URL" \
        --retries 10 --timeout 300 \
        -r /srv/jupyterhub/requirements.txt

# Смоук-тест: если какой-то пакет не установился/не импортируется —
# сборка образа падает здесь, а не в ноутбуке у пользователя.
COPY check_packages.py /srv/jupyterhub/check_packages.py
RUN python3 /srv/jupyterhub/check_packages.py

# Включаем nbdime (человекочитаемые git diff/merge для .ipynb) системно —
# работает сразу для всех Linux-пользователей, создаваемых в рантайме.
RUN python3 -m nbdime config-git --enable --system

# users.txt НЕ копируется в образ: он монтируется как volume в docker-compose.yml
# и пользователи создаются entrypoint.sh при СТАРТЕ контейнера. Так пароли не
# оседают в слоях образа (docker history) и правятся без пересборки.
COPY create_users.sh /srv/jupyterhub/create_users.sh
RUN chmod +x /srv/jupyterhub/create_users.sh

COPY entrypoint.sh /srv/jupyterhub/entrypoint.sh
RUN chmod +x /srv/jupyterhub/entrypoint.sh

# Обёртка запуска notebook-сервера с ограничением памяти на процесс (ulimit -v)
COPY limited-launch.sh /srv/jupyterhub/limited-launch.sh
RUN chmod +x /srv/jupyterhub/limited-launch.sh

COPY templates/ /srv/jupyterhub/templates/

WORKDIR /srv/jupyterhub

ENTRYPOINT ["/srv/jupyterhub/entrypoint.sh"]
CMD ["jupyterhub", "-f", "/srv/jupyterhub/jupyterhub_config.py"]
