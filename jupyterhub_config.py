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

# c.Spawner.mem_limit/cpu_limit сами по себе — информационные поля:
# LocalProcessSpawner (используется здесь) их не enforce'ит, это работает
# только со спавнерами вроде DockerSpawner/KubeSpawner/SystemdSpawner.
#
# Реальное ограничение памяти на процесс сделано отдельно: c.Spawner.cmd
# указывает на limited-launch.sh, который перед запуском
# jupyterhub-singleuser выставляет `ulimit -v` (RLIMIT_AS). Это лимит НА
# ПРОЦЕСС (каждое ядро/каждый notebook-сервер), а не суммарно на
# пользователя — если пользователь откроет несколько ноутбуков одновременно,
# у каждого будет свой лимит. Для точного суммарного лимита на пользователя
# нужны cgroups, то есть переход на DockerSpawner/KubeSpawner.
c.Spawner.cmd = ["/srv/jupyterhub/limited-launch.sh"]
c.Spawner.environment = {
    "JUPYTERHUB_USER_MEM_LIMIT_MB": os.environ.get("JUPYTERHUB_USER_MEM_LIMIT_MB", "2048"),
    # AI-ассистент (Jupyter AI) в каждом пользовательском сервере: ключ
    # Anthropic и адрес Ollama берутся из окружения хаба (см. docker-compose.yml).
    "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
    "OLLAMA_HOST": os.environ.get("OLLAMA_HOST", "http://ollama:11434"),
}
c.Spawner.cpu_limit = 1  # информационно, см. выше

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
