import os

from electrum_scribe.simple_config import SimpleConfig
from electrum_scribe import constants
from electrum_scribe.daemon import Daemon
from electrum_scribe.storage import WalletStorage
from electrum_scribe.wallet import Wallet, create_new_wallet
from electrum_scribe.commands import Commands


config = SimpleConfig({"testnet": True})  # to use ~/.electrum-scribe/testnet as datadir
constants.set_testnet()  # to set testnet magic bytes
daemon = Daemon(config, listen_jsonrpc=False)
network = daemon.network
assert network.asyncio_loop.is_running()

# get wallet on disk
wallet_dir = os.path.dirname(config.get_wallet_path())
wallet_path = os.path.join(wallet_dir, "test_wallet")
if not os.path.exists(wallet_path):
    create_new_wallet(path=wallet_path, config=config)

# open wallet
storage = WalletStorage(wallet_path)
wallet = Wallet(storage, config=config)
wallet.start_network(network)

# you can use ~CLI commands by accessing command_runner
command_runner = Commands(config=config, daemon=daemon, network=network)
command_runner.wallet = wallet
print("balance", command_runner.getbalance())
print("addr",    command_runner.getunusedaddress())
print("gettx",   command_runner.gettransaction("1e9217f2772b7cb93ec71a3201c562e5c4f693c2b7fd0dd956e0c7e640bbb0d0"))

# but you might as well interact with the underlying methods directly
print("balance", wallet.get_balance())
print("addr",    wallet.get_unused_address())
print("gettx",   network.run_from_another_thread(network.get_transaction("1e9217f2772b7cb93ec71a3201c562e5c4f693c2b7fd0dd956e0c7e640bbb0d0")))
