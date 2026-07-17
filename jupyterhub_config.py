import os
import sys

c = get_config()  # noqa

c.JupyterHub.ip = "0.0.0.0"
c.JupyterHub.port = 8000

# --- Аутентификация по системным паролям Linux-пользователей ---
c.JupyterHub.authenticator_class = "jupyterhub.auth.PAMAuthenticator"
c.PAMAuthenticator.open_sessions = False

USERS_FILE = "/srv/jupyterhub/users.txt"

allowed_users = set()
if os.path.exists(USERS_FILE):
    with open(USERS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            allowed_users.add(line.split(":", 1)[0].strip())

c.Authenticator.allowed_users = allowed_users
c.Authenticator.admin_users = {"admin"}

# --- Спавнер: каждый пользователь получает свой notebook-процесс ---
c.Spawner.default_url = "/lab"
c.Spawner.notebook_dir = "/home/{username}/work"

# Ограничения ресурсов носят информационный характер: LocalProcessSpawner
# (используется здесь) НЕ обеспечивает принудительное ограничение CPU/RAM —
# это реально работает только со спавнерами вроде DockerSpawner/KubeSpawner/
# SystemdSpawner. Единственное реальное ограничение на этом стенде — лимит
# на весь контейнер целиком (mem_limit/cpus в docker-compose.yml).
c.Spawner.mem_limit = "2G"
c.Spawner.cpu_limit = 1

# --- Автоматическая очистка неактивных серверов пользователей ---
c.JupyterHub.services = [
    {
        "name": "idle-culler",
        "admin": True,
        "command": [
            sys.executable,
            "-m",
            "jupyterhub_idle_culler",
            "--timeout=3600",   # считать сервер неактивным через 1 час
            "--cull-every=300", # проверять каждые 5 минут
        ],
    }
]

# --- Постоянное хранение состояния хаба (БД, cookie secret) ---
c.JupyterHub.db_url = "sqlite:////srv/jupyterhub/data/jupyterhub.sqlite"
c.JupyterHub.cookie_secret_file = "/srv/jupyterhub/data/jupyterhub_cookie_secret"
