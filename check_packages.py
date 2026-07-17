"""Смоук-тест: убеждается, что все пакеты из requirements.txt реально
импортируются тем же Python, который будет использовать JupyterHub.
Запускается на этапе сборки образа — при поломке падает docker build,
а не тетрадка пользователя после релиза."""

import importlib
import sys

# pip-имя -> имя модуля для import (там, где они отличаются)
PACKAGES = {
    "jupyterlab": "jupyterlab",
    "notebook": "notebook",
    "numpy": "numpy",
    "pandas": "pandas",
    "scipy": "scipy",
    "polars": "polars",
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
}

failed = []
for pip_name, module_name in PACKAGES.items():
    try:
        importlib.import_module(module_name)
    except ImportError as exc:
        failed.append(f"{pip_name} (import {module_name}): {exc}")

if failed:
    print("Не импортируются пакеты:", file=sys.stderr)
    for line in failed:
        print(f"  - {line}", file=sys.stderr)
    sys.exit(1)

print(f"OK: {len(PACKAGES)} пакетов успешно импортированы ({sys.executable})")
