"""
Задание 1. Синхронно vs асинхронно

Замеры:
    sync  (requests, по очереди):          26.46 s
    async (httpx.AsyncClient + TaskGroup):  1.41 s

Объяснение разницы:
    В sync-версии запросы идут по очереди и время ожидания всех 20 ответов
    складывается, а в async все запросы ждут ответа одновременно, поэтому
    общее время примерно равно времени самого медленного запроса.
"""

import asyncio
import time

import httpx
import requests

URLS = [f"https://picsum.photos/seed/{i}/800/600" for i in range(20)]


def timed(label, fn, *args):
    start = time.perf_counter()
    fn(*args)
    print(f"{label}: {time.perf_counter() - start:.2f}s")


async def fetch(client: httpx.AsyncClient, url: str) -> int:
    resp = await client.get(url)
    return resp.status_code


def sync_main():
    for url in URLS:
        requests.get(url)


async def fast_main():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        async with asyncio.TaskGroup() as tg:
            for url in URLS:
                tg.create_task(fetch(client, url))


if __name__ == "__main__":
    timed("sync ", sync_main)
    timed("async", lambda: asyncio.run(fast_main()))