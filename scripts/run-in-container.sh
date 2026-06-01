#!/usr/bin/env bash
# AI: Run a command (or open a shell) inside the running parseltongue dev container.
# AI:
# AI: The container's sshd is NOT forwarded to a host port; only the gem port (5433)
# AI: is published. So we connect directly to the container's IP on the docker bridge
# AI: network, as the 'developer' account, using the developer's configured ssh keys.
# AI:
# AI: The container IP can change when the container is recreated. Override it with
# AI:   PT_HOST=172.x.y.z scripts/run-in-container.sh ...
# AI: To rediscover it, look for the bridge IP whose container has /home/developer/src
# AI: bind-mounted (that is the parseltongue repo).
# AI:
# AI: Usage:
# AI:   scripts/run-in-container.sh                 # interactive login shell in the repo
# AI:   scripts/run-in-container.sh pytest -q       # run a command in a login shell
set -euo pipefail

PT_HOST="${PT_HOST:-172.26.0.2}"
PT_USER="${PT_USER:-developer}"
# AI: The repository is bind-mounted here by docker-compose.yaml.
PT_SRC="${PT_SRC:-/home/developer/src}"

ssh_options=(
    -o StrictHostKeyChecking=no
    -o UserKnownHostsFile=/dev/null
    -o LogLevel=ERROR
    -o ConnectTimeout=10
)

if [ "$#" -eq 0 ]; then
    # AI: No command given: open an interactive login shell in the source directory.
    exec ssh -t "${ssh_options[@]}" "$PT_USER@$PT_HOST" \
        "cd '$PT_SRC' && exec bash -l"
fi

# AI: Encode the command so arbitrary quoting survives the trip to the remote shell.
# AI: It runs in a login shell (so GEMSTONE and friends are defined) from the repo,
# AI: with DEV_USER set as docker-compose.yaml specifies (the login shell omits it).
remote_script="export DEV_USER='$PT_USER'; cd '$PT_SRC' && $*"
encoded_script="$(printf '%s' "$remote_script" | base64 | tr -d '\n')"
exec ssh "${ssh_options[@]}" "$PT_USER@$PT_HOST" \
    "printf '%s' '$encoded_script' | base64 -d | bash -l"
