#!/bin/bash
set -euo pipefail

USERS_FILE="/srv/jupyterhub/users.txt"

# Примонтированные с хоста домашние папки могут принадлежать root —
# приводим владельца в соответствие с пользователем контейнера.
while IFS=: read -r username _ || [ -n "$username" ]; do
  username="$(echo "$username" | xargs)"
  [ -z "$username" ] && continue
  case "$username" in \#*) continue ;; esac

  if [ -d "/home/${username}" ]; then
    mkdir -p "/home/${username}/work"
    if [ ! -f "/home/${username}/work/welcome.ipynb" ] && [ -f /srv/jupyterhub/templates/welcome.ipynb ]; then
      cp /srv/jupyterhub/templates/welcome.ipynb "/home/${username}/work/welcome.ipynb"
    fi
    chown -R "${username}:${username}" "/home/${username}"
  fi
done < "$USERS_FILE"

mkdir -p /srv/shared
chmod 1777 /srv/shared

mkdir -p /srv/jupyterhub/data

exec "$@"
