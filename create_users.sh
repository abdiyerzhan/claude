#!/bin/bash
set -euo pipefail

USERS_FILE="/srv/jupyterhub/users.txt"

while IFS=: read -r username password || [ -n "$username" ]; do
  username="$(echo "$username" | xargs)"
  [ -z "$username" ] && continue
  case "$username" in \#*) continue ;; esac

  if ! id "$username" &>/dev/null; then
    useradd -m -s /bin/bash "$username"
  fi
  echo "${username}:${password}" | chpasswd
  mkdir -p "/home/${username}/work"
  chown -R "${username}:${username}" "/home/${username}"
done < "$USERS_FILE"
