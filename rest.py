import requests
import asyncio
import json
import aiocron
from datetime import date
from dateutil.relativedelta import relativedelta
from redis import RedisConnection

api_endpoint = 'https://api.skypicker.com/flights'
booking_api_endpoint = 'https://booking-api.skypicker.com/api/v0.1/check_flights'
headers = {'Content-Type': 'application/json'}

# directions = [
#     'ALA-TSE', 'TSE-ALA', 'ALA-MOW', 'MOW-ALA', 'ALA-CIT', 
#     'CIT-ALA', 'TSE-MOW', 'MOW-TSE', 'TSE-LED', 'LED-TSE'
# ]

directions = [
    'ALA-TSE', 'TSE-ALA'
]


async def update_direction(connection, from_city, to_city, date_from, date_to):
    params = {
        'fly_from' : from_city,
        'fly_to' : to_city, 
        'date_from' : date_from, 
        'date_to' : date_to, 
        'adults' : 1,
        'partner' : 'picky'
    }

    data = requests.get(api_endpoint, params=params)
    
    await connection.set(f"{from_city}-{to_city}", json.dumps(data.json()))


# @aiocron.crontab('0 0 0 * *')
async def update_redis():
    connection = (await RedisConnection()).connection
    
    date_from = date.today()
    date_to = date_from + relativedelta(months =+ 1)

    date_from = f"{date_from.day}/{date_from.month}/{date_from.year}"
    date_to = f"{date_to.day}/{date_to.month}/{date_to.year}"

    tasks = []

    for direction in directions:
        from_city, to_city = direction.split('-')

        task = asyncio.create_task(
            update_direction(connection, from_city, to_city, date_from, date_to)
        )
        
        tasks.append(task)
    
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(update_redis())