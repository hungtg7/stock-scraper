import time
import os
import pandas
import asyncio
import aiohttp
from glob import glob

from loguru import logger

from utils.df import transform

url = "https://trading.kisvn.vn/rest/api/v2/market/symbol/{}/quote"
storage_path = "vn_stock/storage/{}/{}.csv"
monitor_path = "vn_stock/storage/monitor.csv"
name = ['ACB', 'BID', 'BVH', 'CTG', 'FPT', 'GAS', 'GVR', 'HDB', 'HPG',
        'KDH', 'MBB', 'MSN', 'MWG', 'NVL', 'PDR',
        'PLX', 'PNJ', 'POW', 'SAB', 'SSI', 'STB',
        'TCB', 'TPB', 'VCB', 'VHM', 'VIC', 'VJC', 'VNM', 'VPB', 'VRE']


def get_data_task(session):
    tasks = []
    logger.info("Get Data...")
    for n in name:
        tasks.append(get_data(n, session))

    return tasks


def monitor_data_task():
    logger.info("Monitor Data...")
    tasks = []
    for n in name:
        tasks.append(monitor_data(n))

    return tasks


async def monitor_data(n: str):
    try:
        df1 = pandas.read_csv(storage_path.format("data", n), index_col=False)
    except Exception:
        df1 = None
        print(f"{df1} dont have data")
        return

    total_vol = df1["vo"]
    max_vol = total_vol.max()
    total_matchin_vol = df1["mv"].sum()
    d = {'name': [n], 'diff_vol': [max_vol - total_matchin_vol]}
    df = pandas.DataFrame(d)
    df.to_csv(storage_path.format("monitor_result", n), index=False)
    return


async def get_data(n, session):
    resp = await session.get(url.format(n), ssl=False)
    content = await resp.json()
    df = pandas.DataFrame(content)
    df = transform.sor_by_col(df, col="vo")
    df = transform.transform_t_col(df, "t", )

    try:
        df1 = pandas.read_csv(storage_path.format("data", n), index_col=False)
    except Exception:
        df1 = None

    df = transform.upsert(df1, df)
    df.to_csv(storage_path.format("data", n), index=False)


async def call_api():
    async with aiohttp.ClientSession() as session:
        get_tasks = get_data_task(session)
        monitor_task = monitor_data_task()
        await asyncio.gather(*get_tasks, *monitor_task)


def concat_monitor_result():
    all_files = glob(
        storage_path.format("monitor_result", "*"))

    li = []

    for filename in all_files:
        df = pandas.read_csv(filename, index_col=None, header=0)
        li.append(df)

    frame = pandas.concat(li, axis=0, ignore_index=True)

    frame.to_csv(monitor_path)


if __name__ == "__main__":
    while True:
        asyncio.run(call_api())
        concat_monitor_result()
        logger.info("Done\n+++++++++++++++++++++++++++++++++++++++\n")
        time.sleep(10)
