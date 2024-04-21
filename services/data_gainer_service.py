import asyncio
import copy
import datetime
from datetime import datetime, timedelta

import aiohttp
import pandas as pd
import requests
from pybit import unified_trading

from services.config import broker_config


def get_tradeable_symbols():
    broker_session = unified_trading.HTTP(
        api_key=broker_config.BROKER_API_KEY,
        api_secret=broker_config.BROKER_API_SECRET,
        testnet=False,
    )

    sym_list = []
    symbols = broker_session.get_tickers(category="linear")
    if "retMsg" in symbols.keys():
        if symbols["retMsg"] == "OK":
            for symbol in symbols["result"]["list"]:
                sym_list.append(symbol["symbol"])

    return sym_list


async def fetch(async_session, url):
    async with async_session.get(url) as response:
        to_return = await response.json()
        return to_return["result"]["list"]


async def async_past_data_gainer(**kwargs) -> pd.DataFrame:
    start = kwargs.get("start")
    end = kwargs.get("end")
    interval = kwargs.get("interval")
    ticker = kwargs.get("ticker")

    responses: list = list()
    difference = end - start

    limit = int(
        int(difference.days * 1440 / int(interval) + 1)
        + difference.seconds / 60 / interval
    )
    mid_date = copy.copy(start)
    target_urls = []
    while limit > 1000:
        mid_limit = 1000
        mid_date = mid_date + timedelta(seconds=mid_limit * interval * 60 - interval)

        start_timestamp = int(start.timestamp()) * 1000
        end_timestamp = int(mid_date.timestamp()) * 1000

        target_urls.append(
            f"https://api-testnet.bybit.com/v5/market/kline?category=linear&symbol={ticker}&"
            f"interval={interval}&limit={int(mid_limit)}&start={start_timestamp}&end={end_timestamp}"
        )

        limit += -1000

    loop = asyncio.get_event_loop()
    async with aiohttp.ClientSession(loop=loop) as async_session:
        tasks = [loop.create_task(fetch(async_session, url)) for url in target_urls]
        results = await asyncio.gather(*tasks)
    to_append = []
    for result in results:
        to_append += [item for item in result]

    responses += to_append

    mid_date = mid_date + timedelta(seconds=limit * interval * 60)
    start_timestamp = int(start.timestamp()) * 1000
    end_timestamp = int(mid_date.timestamp()) * 1000

    url = (
        f"https://api-testnet.bybit.com/v5/market/kline?category=linear&symbol={ticker}&"
        f"interval={interval}&limit={int(limit)}&start={start_timestamp}&end={end_timestamp}"
    )
    responses += requests.request("GET", url, headers={}, data={}).json()["result"][
        "list"
    ]
    # print(len(responses))
    data = [
        [
            datetime.fromtimestamp(int(item[0][:-3])),
            float(item[1]),
            float(item[2]),
            float(item[3]),
            float(item[4]),
            float(item[5]),
        ]
        for item in responses
    ]

    columns = ["Date", "Open", "High", "Low", "Close", "Volume"]

    df = pd.DataFrame(data, columns=columns)
    df.sort_values("Date", ascending=True, inplace=True)
    df.reset_index(inplace=True, drop=True)
    return df


def get_past_data(**kwargs) -> pd.DataFrame:
    return asyncio.run(async_past_data_gainer(**kwargs))
