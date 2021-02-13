import asyncio, json, aiocron
from datetime import date
from dateutil.relativedelta import relativedelta
from redis import RedisConnection
from aiohttp import ClientSession
from aiohttp_cache import (
    setup_cache, 
    setup
)

api_endpoint = 'https://api.skypicker.com/flights'
booking_api_endpoint = 'https://booking-api.skypicker.com/api/v0.1/check_flights'
headers = {'Content-Type': 'application/json'}

directions = (
    'ALA-TSE', 'TSE-ALA', 'ALA-MOW', 'MOW-ALA', 'ALA-CIT', 
    'CIT-ALA', 'TSE-MOW', 'MOW-TSE', 'TSE-LED', 'LED-TSE'
)

locations = (
    'ALA', 'TSE', 'MOW', 'CIT', 'LED'
)


async def update_direction(connection, from_city, to_city, date_from, date_to):
    params = {
        'fly_from' : from_city,
        'fly_to' : to_city, 
        'date_from' : date_from, 
        'date_to' : date_to, 
        'adults' : 1,
        'partner' : 'picky'
    }

    async with ClientSession() as session:
        async with session.get(api_endpoint, params=params) as response:
            data = await response.json()
            await connection.set(f"{from_city}-{to_city}", json.dumps(data))
    

@aiocron.crontab('0 0 0 * *')
async def autoupdate_redis():
    print('UPDATE')
    connection = (await RedisConnection()).connection
    
    date_from = date.today()
    date_to = date_from + relativedelta(months =+ 1)

    date_from = f"{date_from.day}/{date_from.month}/{date_from.year}"
    date_to = f"{date_to.day}/{date_to.month}/{date_to.year}"

    tasks = [
        asyncio.create_task(
            update_direction(
                connection, 
                direction[:3], direction[4:], 
                date_from, date_to
            )
        )
        for direction in directions
    ]

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(autoupdate_redis())