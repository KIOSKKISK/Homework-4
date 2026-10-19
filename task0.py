"""
Задание 0. Разминка-ловушка «Почему не быстрее?»

Замеры:
    slow  (await в цикле for): 9.92 s
    fixed (asyncio.gather):    1.34 s

Почему async не дал ускорения:
    В slow_main await стоит прямо внутри цикла for. await ждёт, пока
    придёт ответ, и только потом цикл переходит к следующему URL. Поэтому
    запросы идут строго по очереди, как в обычном синхронном коде, и время
    всех 20 запросов складывается.

Как починил:
    В fixed_main все 20 запросов запускаются одновременно через
    asyncio.gather. Пока один запрос ждёт ответа сервера, остальные тоже
    уже отправлены, поэтому общее время примерно равно времени самого
    медленного запроса. Получилось примерно в 7 раз быстрее.
    follow_redirects=True нужен, потому что picsum отвечает редиректом 302,
    а httpx сам по нему не переходит.
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


async def slow_main():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        for url in URLS:
            await fetch(client, url)


async def fixed_main():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        await asyncio.gather(*(fetch(client, url) for url in URLS))


timed("slow ", lambda: asyncio.run(slow_main()))
timed("fixed", lambda: asyncio.run(fixed_main()))