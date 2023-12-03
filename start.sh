#!/usr/bin/env bash


usage() {
cat << EOF
Adsfree fly.io based app entrypoint

Usage:
    ${0} [OPTIONS]

Options:
    --python    Use python DNS over HTTPS relay
    --rust      Use rust DNS over HTTPS relay
    --help      Show help message
EOF
}


while [ "${#}" -gt 0 ]; do
    case "${1}" in
        -h|--help)
            usage
            exit
            ;;

        --python)
            PYTHON=1
            ;;

        --rust)
            RUST=1
            ;;

        *)
            echo "Unreconginzed argument: ${1}"
            usage
            exit 1
            ;;
    esac
    
   shift
done

set -exuo pipefail

VOLUMIZED_DIRS=("/etc/pihole" "/etc/dnsmasq.d")

for dir in ${VOLUMIZED_DIRS[@]}; do
    target_in_volume="$PH_VOLUME$dir"
    
    if [ ! -d "$target_in_volume" ]; then
        mkdir -p $(dirname "$target_in_volume")
        mv "$dir" "$target_in_volume"
    else
        rm -rf "$dir"
    fi
    
    ln -s "$target_in_volume" "$dir"
done

if [ -n "${PYTHON+x}" ]; then
    python3 -u /app/doh_relay.py > /app/doh_relay.log 2>&1 &
elif [ -n "${RUST+x}" ]; then
    /app/relay > /app/doh_relay.log 2>&1 &
else 
    usage
    exit 1
fi

/app/wait-for-it.sh --host=127.0.0.1 --port=8000 -t 5

# See https://github.com/pi-hole/docker-pi-hole/issues/1176#issuecomment-1232363970 
unshare --pid --fork --kill-child=SIGTERM --mount-proc perl -e "\$SIG{INT}=''; \$SIG{TERM}=''; exec @ARGV;" -- /s6-init

