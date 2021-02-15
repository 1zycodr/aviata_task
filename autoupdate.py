import asyncio, json, aiocron
from json import JSONDecodeError
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

# directions = (
#     'ALA-TSE',
# )

directions = (
    'ALA-TSE', 'TSE-ALA', 'ALA-MOW', 'MOW-ALA', 'ALA-CIT',
    'CIT-ALA', 'TSE-MOW', 'MOW-TSE', 'TSE-LED', 'LED-TSE'
)

locations = (
    'ALA', 'TSE', 'MOW', 'CIT', 'LED'
)


async def confirm_flight(session, flight):
    params = {
        'pnum' : 1, 
        'bnum' : 1, 
        'adults' : 1,
        'booking_token' : flight['booking_token']
    }
    attempts = 15

    print('Checking', flight['flyFrom'] + '->' + flight['flyTo'], flight['id'], sep='\t')

    while attempts != 0:
        async with session.get(booking_api_endpoint, params=params, headers=headers) as response_booking:
            try:
                flight_data = json.loads(await response_booking.read())
            except Exception as ex:
                # handle temporary ban
                print('NONE')
                with open('errors.txt', 'a') as file:
                    file.write(str(ex))
                    file.write('\n')
                return None
                

            if flight_data['flights_checked']:
                if not flight_data['flights_invalid']:
                    print('Checked ', flight['flyFrom'] + '->' + flight['flyTo'], flight['id'], sep='\t')
                    return flight_data
                else:
                    print('Checked INVALID', flight['flyFrom'] + '->' + flight['flyTo'], flight['id'], sep='\t')
                    return None
            else:
                print('Rechecking', flight['flyFrom'] + '->' + flight['flyTo'], flight['id'], sep='\t')
                attempts -= 1
                await asyncio.sleep(10)
    

async def update_direction(connection, from_city, to_city, date_from, date_to, delay):
    # await asyncio.sleep(delay)

    params = {
        'fly_from' : from_city,
        'fly_to' : to_city, 
        'date_from' : date_from, 
        'date_to' : date_to, 
        'adults' : 1,
        'partner' : 'picky'
    }
        
    
    async with ClientSession() as session:
        async with session.get(api_endpoint, params=params, headers=headers) as response:
            
            data = await response.json()
            flights = data['data']

            # confirm_flights_tasks = [
            #     asyncio.create_task(
            #         confirm_flight(session, flight)
            #     )
            #     for flight in flights
            # ]

            # flights_copy = await asyncio.gather(*confirm_flights_tasks)

            # flights_copy = [
            #     flight 
            #     for flight in flights_copy 
            #     if flight is not None
            # ]

            flights_copy = [
                await confirm_flight(session, flight)
                for flight in flights
            ]

            flights_copy = [
                flight 
                for flight in flights_copy
                if flight is not None
            ]

            data['data'] = flights_copy

            await connection.set(f"{from_city}-{to_city}", json.dumps(data))


@aiocron.crontab('0 0 0 * *')   
async def autoupdate_redis():
    connection = (await RedisConnection()).connection
    
    date_from = date.today()
    date_to = date_from + relativedelta(months =+ 1)

    date_from = f"{date_from.day}/{date_from.month}/{date_from.year}"
    date_to = f"{date_to.day}/{date_to.month}/{date_to.year}"

    update_tasks = [
        asyncio.create_task(
            update_direction(
                connection, 
                direction[:3], direction[4:], 
                date_from, date_to, 
                delay * 2
            )
        )
        for delay, direction in enumerate(directions)
    ]

    await asyncio.gather(*update_tasks)


if __name__ == '__main__':
    asyncio.run(autoupdate_redis())