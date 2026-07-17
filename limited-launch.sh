#!/bin/bash
# Оборачивает запуск notebook-сервера пользователя ограничением памяти.
# С LocalProcessSpawner (используется в этом стенде) единственный способ
# реально ограничить память процесса без перехода на DockerSpawner/KubeSpawner
# (там лимит через cgroups) — RLIMIT_AS через `ulimit -v`.
set -e

MEM_LIMIT_MB="${JUPYTERHUB_USER_MEM_LIMIT_MB:-2048}"
ulimit -v $(( MEM_LIMIT_MB * 1024 ))

exec jupyterhub-singleuser "$@"
