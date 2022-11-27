import json
import os
from pathlib import Path
from string import Template

import ccxt
from pycoingecko import CoinGeckoAPI

stake_currency = os.getenv("STAKE_CURRENCY", "USDT")
exchange = os.getenv("EXCHANGE", "binance")
pair_number = os.getenv("PAIR_NUMBER", 100)
output_file_name = os.getenv("OUTPUT_FILE_NAME", "marketcap_pairlist.json")

template_json = Template(
    """
{
    "exchange": {
        "name": "$exchange",
        "pair_whitelist": [
            $pair_list
        ],
        "pair_blacklist": [
            // Exchange
            "(BNB)/.*",
            // Leverage
            ".*(_PREMIUM|BEAR|BULL|HALF|HEDGE|UP|DOWN|[1235][SL])/.*",
            // Fiat
            "(AUD|BRZ|CAD|CHF|EUR|GBP|HKD|IDRT|JPY|NGN|RUB|SGD|TRY|UAH|USD|ZAR)/.*",
            // Stable
            "(BUSD|CUSD|CUSDT|DAI|PAXG|SUSD|TUSD|USDC|USDN|USDP|USDT|VAI|UST|USTC|AUSD)/.*",
            // FAN
            "(ACM|AFA|ALA|ALL|ALPINE|APL|ASR|ATM|BAR|CAI|CHZ|CITY|FOR|GAL|GOZ|IBFK|JUV|LEG|LOCK-1|NAVI|NMR|NOV|PFL|PSG|ROUSH|STV|TH|TRA|UCH|UFC|YBO)/.*",
            // Others
            "(BTC|VIDT|1EARTH|ILA|BOBA|CTXC|CWAR|ARDR|DMTR|MLS|TORN|ANC|LUNA|BTS|QKC|COS|ACA|FTT)/.*"
        ]
    },
    "pairlists": [
        {
            "method": "StaticPairList"
        },
        {
            "method": "AgeFilter",
            "min_days_listed": 200
        },
        {
            "method": "RangeStabilityFilter",
            "lookback_days": 3,
            "min_rate_of_change": 0.03,
            "refresh_period": 1800
        },
        {
            "method": "VolatilityFilter",
            "lookback_days": 3,
            "min_volatility": 0.01,
            "max_volatility": 0.75,
            "refresh_period": 43200
        },
        {
            "method": "ShuffleFilter"
        }
    ],
    "dataformat_ohlcv": "hdf5",
    "dataformat_trades": "hdf5"
}
"""
)


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
    Path(f"{output_file_name}").write_text(
        json.dumps(
            template_json.substitute(
                exchange=exchange, pair_list=get_top_coins_by_market_cap()
            ),
            indent=4,
        )
    )


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
