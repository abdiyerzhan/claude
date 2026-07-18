"""Смоук-тест: убеждается, что все пакеты из requirements*.txt реально
импортируются тем же Python, который будет использовать JupyterHub.
Запускается на этапе сборки образа — при поломке падает docker build,
а не тетрадка пользователя после релиза.

Каждый пакет импортируется в ОТДЕЛЬНОМ подпроцессе: некоторые сборки
(например, обычный polars на CPU без AVX2) падают не с ImportError, а с
сигналом уровня ОС (SIGILL/Illegal instruction), который try/except в
одном процессе не ловит и убивает всю проверку разом. По отдельности —
один упавший пакет не мешает увидеть остальные."""

import subprocess
import sys

# pip-имя -> имя модуля для import (там, где они отличаются)
PACKAGES = {
    "jupyterlab": "jupyterlab",
    "notebook": "notebook",
    "numpy": "numpy",
    "pandas": "pandas",
    "scipy": "scipy",
    "polars-lts-cpu": "polars",
    "openpyxl": "openpyxl",
    "pyarrow": "pyarrow",
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
    "plotly": "plotly",
    "scikit-learn": "sklearn",
    "statsmodels": "statsmodels",
    "xgboost": "xgboost",
    "lightgbm": "lightgbm",
    "requests": "requests",
    "tqdm": "tqdm",
    "python-dotenv": "dotenv",
    "oracledb": "oracledb",
    "psycopg2-binary": "psycopg2",
    "duckdb": "duckdb",
    "sqlalchemy": "sqlalchemy",
    "jupysql": "sql",
    "xlsxwriter": "xlsxwriter",
    "itables": "itables",
    "jupyterlab-git": "jupyterlab_git",
    "nbdime": "nbdime",
    "ipywidgets": "ipywidgets",
    "jupyterlab-lsp": "jupyterlab_lsp",
    "python-lsp-server": "pylsp",
    "jupyterhub-idle-culler": "jupyterhub_idle_culler",
    "jupyter-ai": "jupyter_ai",
    "langchain-anthropic": "langchain_anthropic",
    "langchain-ollama": "langchain_ollama",
    "langchain-openai": "langchain_openai",
    "langchain-google-genai": "langchain_google_genai",
}

failed = []
for pip_name, module_name in PACKAGES.items():
    result = subprocess.run(
        [sys.executable, "-c", f"import {module_name}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode != 0:
        reason = result.stdout.decode(errors="replace").strip().splitlines()
        last_line = reason[-1] if reason else ""
        if result.returncode < 0:
            last_line += f" (сигнал {-result.returncode}, например SIGILL — обычно несовместимость сборки с CPU)"
        failed.append(f"{pip_name} (import {module_name}, код {result.returncode}): {last_line}")

if failed:
    print("Не импортируются пакеты:", file=sys.stderr)
    for line in failed:
        print(f"  - {line}", file=sys.stderr)
    sys.exit(1)

print(f"OK: {len(PACKAGES)} пакетов успешно импортированы ({sys.executable})")
