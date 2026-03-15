import getpass
import json
import os

import eth_account
from eth_account.signers.local import LocalAccount

from hyperliquid.exchange import Exchange
from hyperliquid.info import Info

import pandas as pd
import time
import math



def setup(base_url=None, skip_ws=False, perp_dexs=None):
    secret_key = os.environ["HL_SECRET"]
    wallet = os.environ["HL_WALLET"]
    
    account: LocalAccount = eth_account.Account.from_key(secret_key)
    address = wallet 
    if address == "":
        address = account.address
    print("Running with account address:", address)
    if address != account.address:
        print("Running with agent address:", account.address)
    info = Info(base_url, skip_ws, perp_dexs=perp_dexs)
    user_state = info.user_state(address)
    spot_user_state = info.spot_user_state(address)
    margin_summary = user_state["marginSummary"]
    if float(margin_summary["accountValue"]) == 0 and len(spot_user_state["balances"]) == 0:
        print("Not running the example because the provided account has no equity.")
        url = info.base_url.split(".", 1)[1]
        error_string = f"No accountValue:\nIf you think this is a mistake, make sure that {address} has a balance on {url}.\nIf address shown is your API wallet address, update the config to specify the address of your account, not the address of the API wallet."
        raise Exception(error_string)
    equity_perp = float(user_state["marginSummary"]["accountValue"])
    exchange = Exchange(account, base_url, account_address=address, perp_dexs=perp_dexs)
    return address, info, exchange, equity_perp


def get_secret_key(config):
    if config["secret_key"]:
        secret_key = config["secret_key"]
    else:
        keystore_path = config["keystore_path"]
        keystore_path = os.path.expanduser(keystore_path)
        if not os.path.isabs(keystore_path):
            keystore_path = os.path.join(os.path.dirname(__file__), keystore_path)
        if not os.path.exists(keystore_path):
            raise FileNotFoundError(f"Keystore file not found: {keystore_path}")
        if not os.path.isfile(keystore_path):
            raise ValueError(f"Keystore path is not a file: {keystore_path}")
        with open(keystore_path) as f:
            keystore = json.load(f)
        password = getpass.getpass("Enter keystore password: ")
        secret_key = eth_account.Account.decrypt(keystore, password)
    return secret_key


def setup_multi_sig_wallets():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path) as f:
        config = json.load(f)

    authorized_user_wallets = []
    for wallet_config in config["multi_sig"]["authorized_users"]:
        account: LocalAccount = eth_account.Account.from_key(wallet_config["secret_key"])
        address = wallet_config["account_address"]
        if account.address != address:
            raise Exception(f"provided authorized user address {address} does not match private key")
        print("loaded authorized user for multi-sig", address)
        authorized_user_wallets.append(account)
    return authorized_user_wallets


def klines(info, symbol, timeframe='5m', interval=500):
    intervals = {'1m': 60000,
                 '3m': 180000,
                 '5m': 300000,
                 '15m': 900000,
                 '30m': 1800000,
                 '1h': 3600000,
                 '2h': 7200000,
                 '4h': 14400000,
                 '8h': 28800000,
                 '12h': 43200000,
                 '1d': 86400000,
                 '3d': 259200000,
                 '1w': 604800000,
                 }

    start = round(time.time() * 1000) - intervals[timeframe] * interval
    end = round(time.time() * 1000)

    kl = info.candles_snapshot(symbol, timeframe, start, end)
    kl = pd.DataFrame(kl)
    kl = kl.drop('t', axis=1, errors='ignore')
    kl = kl.drop('s', axis=1, errors='ignore')
    kl = kl.drop('i', axis=1, errors='ignore')
    kl.columns = ['Time', 'Open', 'Close', 'High', 'Low', 'Volume', 'N']
    kl = kl.set_index('Time')
    kl.index = pd.to_datetime(kl.index, unit='ms')
    return kl

def market_order(exchange, symbol, isbuy, size):
    order = exchange.market_open(symbol, is_buy=isbuy, sz=size, px=None, slippage=0.01)
    if order["status"] == "ok":
        for status in order["response"]["data"]["statuses"]:
            try:
                filled = status["filled"]
                print(f'Order #{filled["oid"]} filled {filled["totalSz"]} @{filled["avgPx"]}')
            except KeyError:
                print(f'Error: {status["error"]}')

def market_close(exchange, symbol):
    close = exchange.market_close(symbol)
    if close["status"] == "ok":
        for status in close["response"]["data"]["statuses"]:
            try:
                filled = status["filled"]
                print(f'Order #{filled["oid"]} filled {filled["totalSz"]} @{filled["avgPx"]}')
            except KeyError:
                print(f'Error: {status["error"]}')

def decimalPrecision(count_decimals : int, perp_equity : float):
    """Truncate a float to the given number of decimals without rounding"""
    factor = 10 ** count_decimals
    return math.floor(perp_equity * factor) / factor

def isAvailToBuy(perp_equity, MIN_BUY_BTC):
    if (perp_equity < MIN_BUY_BTC):
        print(perp_equity, "is less than" , MIN_BUY_BTC)
        return False
    print("Continue to Buy", perp_equity, "is greater than", MIN_BUY_BTC)

    return True


    