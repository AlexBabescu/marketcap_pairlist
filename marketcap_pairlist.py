import json
import os
from pathlib import Path

import ccxt
from pycoingecko import CoinGeckoAPI

stake_currency = os.getenv("STAKE_CURRENCY", "USDT")
exchange = os.getenv("EXCHANGE", "binance")
pair_number = os.getenv("PAIR_NUMBER", 100)
update_frequency  = os.getenv("UPDATE_FREQUENCY", 24)
output_file_name  = os.getenv("OUTPUT_FILE_NAME", "marketcap_pairlist.json")


def get_top_coins_by_market_cap():
    cg = CoinGeckoAPI()
    top_coins = [
        coin["symbol"].upper() + "/" + stake_currency
        for coin in cg.get_coins_markets(
            vs_currency="usd", order="market_cap_desc", per_page=200, page=1
        )
    ]
    tradable_pairs = get_tradable_pairs()
    top_coins_tradable = [pair for pair in top_coins if pair in tradable_pairs][
        :pair_number
    ]

    return top_coins_tradable


def dump_tradable_pairs():
    payload = {
        "exchange": {"name": f"{exchange}", "pair_whitelist": get_top_coins_by_market_cap()}
    }
    Path(f"{output_file_name}").write_text(json.dumps(payload, indent=4))


def get_tradable_pairs():
    match exchange:
        case "binance":
            ccxt_exchange = ccxt.binance()
        case "kucoin":
            ccxt_exchange = ccxt.kucoin()
        case _:
            raise ValueError("Exchange can only be binance or kucoin")

    ccxt_exchange.load_markets()
    return ccxt_exchange.symbols


if __name__ == "__main__":
    print("Updating pairlist...")
    dump_tradable_pairs()
    print(f"Pairlist updated: {output_file_name}.")
