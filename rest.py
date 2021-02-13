import requests
import asyncio
import json
import aioredis
import aiocron
from datetime import date
from dateutil.relativedelta import relativedelta

today = date.today()
month_day = today + relativedelta(months =+ 1)

directions = [
    'ALA-TSE', 'TSE-ALA', 'ALA-MOW', 'MOW-ALA', 'ALA-CIT', 
    'CIT-ALA', 'TSE-MOW', 'MOW-TSE', 'TSE-LED', 'LED-TSE'
]


async def update_direction(con, from_city, to_city):
    await con.set(f"{from_city}-{to_city}", 'test')


@aiocron.crontab('0 0 0 * *')
async def update_redis():
    con = await aioredis.create_redis('redis://localhost')

    tasks = []

    for direction in directions:
        from_city, to_city = direction.split('-')

        task = asyncio.create_task(
            update_direction(con, from_city, to_city)
        )
        
        tasks.append(task)
    
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(update_redis())