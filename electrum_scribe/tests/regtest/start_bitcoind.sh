#!/usr/bin/env bash
export HOME=~
set -eux pipefail
mkdir -p ~/.scribe
cat > ~/.scribe/scribe.conf <<EOF
regtest=1
txindex=1
printtoconsole=1
rpcuser=doggman
rpcpassword=donkey
rpcallowip=127.0.0.1
zmqpubrawblock=tcp://127.0.0.1:28332
zmqpubrawtx=tcp://127.0.0.1:28333
[regtest]
rpcbind=0.0.0.0
rpcport=19443
EOF
rm -rf ~/.scribe/regtest
screen -S scribed -X quit || true
screen -S scribed -m -d scribed -regtest
sleep 6
addr=$(scribe-cli getnewaddress)
scribe-cli generatetoaddress 150 $addr > /dev/null
