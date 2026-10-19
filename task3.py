"""
Задание 3 (*). Вынос CPU-bound-вычислений

Замеры:
    heavy в лоб (прямо в корутине):         2.93 s  — точки ticker замерли
    heavy через ProcessPoolExecutor:        1.56 s  — точки продолжали бежать
    cpu_main целиком:                       7.14 s

Объяснение:
    heavy — обычная синхронная функция без await. Если вызвать её прямо
    в корутине, event loop не может переключиться на другие задачи, пока
    она считает, поэтому ticker перестаёт печатать точки.
    Через loop.run_in_executor + ProcessPoolExecutor вычисления идут
    в отдельных процессах, а корутина только ждёт результат через await.
    Event loop свободен — точки бегут. Плюс считают несколько ядер сразу,
    поэтому вышло быстрее.
    ThreadPoolExecutor здесь не подходит: потоки упираются в GIL и не
    ускоряют вычисления на процессоре.
"""

import asyncio
import hashlib
import time
from concurrent.futures import ProcessPoolExecutor

import httpx
import requests

URLS = [f"https://picsum.photos/seed/{i}/800/600" for i in range(20)]


def timed(label, fn, *args):
    start = time.perf_counter()
    fn(*args)
    print(f"{label}: {time.perf_counter() - start:.2f}s")


def heavy(body: bytes) -> str:
    return hashlib.sha256(body * 1000).hexdigest()


async def ticker():
    while True:
        print(".", end="", flush=True)
        await asyncio.sleep(0.1)


async def cpu_main():
    tick = asyncio.create_task(ticker())

    print("\n[1] скачиваю картинки:")
    async with httpx.AsyncClient(follow_redirects=True) as client:
        responses = await asyncio.gather(*(client.get(url) for url in URLS))
    bodies = [r.content for r in responses]

    print("\n[2] heavy в лоб (точки замрут):")
    await asyncio.sleep(0.5)
    start = time.perf_counter()
    for body in bodies:
        heavy(body)
    print(f"\n    в лоб: {time.perf_counter() - start:.2f}s")
    await asyncio.sleep(0.5)

    print("\n[3] heavy в отдельных процессах (точки бегут):")
    loop = asyncio.get_running_loop()
    start = time.perf_counter()
    with ProcessPoolExecutor() as pool:
        await asyncio.gather(
            *(loop.run_in_executor(pool, heavy, body) for body in bodies)
        )
    print(f"\n    в процессах: {time.perf_counter() - start:.2f}s")

    tick.cancel()


if __name__ == "__main__":
    timed("cpu  ", lambda: asyncio.run(cpu_main()))