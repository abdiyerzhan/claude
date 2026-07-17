FROM jupyterhub/jupyterhub:4

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-pip \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /srv/jupyterhub/requirements.txt
RUN python3 -m pip install --no-cache-dir -r /srv/jupyterhub/requirements.txt

COPY users.txt /srv/jupyterhub/users.txt
COPY create_users.sh /srv/jupyterhub/create_users.sh
RUN chmod +x /srv/jupyterhub/create_users.sh \
    && /srv/jupyterhub/create_users.sh

COPY entrypoint.sh /srv/jupyterhub/entrypoint.sh
RUN chmod +x /srv/jupyterhub/entrypoint.sh

WORKDIR /srv/jupyterhub

ENTRYPOINT ["/srv/jupyterhub/entrypoint.sh"]
CMD ["jupyterhub", "-f", "/srv/jupyterhub/jupyterhub_config.py"]
