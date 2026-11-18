#!/bin/bash
set -u
pkill -x tor 2>/dev/null || true
sleep 1
rm -rf /tmp/tordata
nohup tor --SocksPort 9050 --ControlPort 9051 --CookieAuthentication 1 --DataDirectory /tmp/tordata --MaxCircuitDirtiness 60 >/tmp/tor.log 2>&1 &
sleep 10
tail -2 /tmp/tor.log
ls -la /tmp/tordata/control_auth_cookie 2>/dev/null || echo "no cookie"
