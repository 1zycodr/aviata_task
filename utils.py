import asyncio
import json
import aiocron
from json import JSONDecodeError
from datetime import date
from dateutil.relativedelta import relativedelta
from redis import RedisConnection
from aiohttp import ClientSession
from aiohttp_cache import (
    setup_cache,
    setup
)
from settings import (
    api_endpoint,
    booking_api_endpoint,
    headers,
    directions,
    max_attempts_to_recheck,
    recheck_delay
)


def get_err_no_direction(from_city, to_city):
    return 'There are no flights between'\
        + f'these locations: `{from_city}`, `{to_city}`'


def get_err_required_mess(param):
    return f"Parameter {param} is a required field, "\
        + "but it was not given."


def get_err_not_recognized_mess(value):
    return f'Not recognized location: `{value}`'


async def confirm_flight(session: ClientSession, flight: dict) -> dict:
    params = {
        'pnum': 1,
        'bnum': 1,
        'adults': 1,
        'booking_token': flight['booking_token']
    }

    attempts = 0

    # trying to confirm flight
    # while flights_checked = false, rechecking with delay
    while attempts != max_attempts_to_recheck:
        async with session.get(
            booking_api_endpoint,
            params=params,
            headers=headers
        ) as response_booking:
            try:
                flight_data = await response_booking.json()
            except Exception as ex:
                # handle temporary ban
                await asyncio.sleep(40)

            if flight_data['flights_checked']:
                if not flight_data['flights_invalid']:
                    # valid flight
                    return flight_data
                else:
                    # invalid flight
                    return None
            else:
                # re-check
                attempts += 1
                await asyncio.sleep(recheck_delay)
    else:
        return None


async def update_direction(
    connection,
    from_city, to_city,
    date_from, date_to,
    delay
):
    # to avoid the temporary ban of the IP address
    await asyncio.sleep(delay)

    params = {
        'fly_from': from_city,
        'fly_to': to_city,
        'date_from': date_from,
        'date_to': date_to,
        'adults': 1,
        'partner': 'picky'
    }

    async with ClientSession() as session:
        async with session.get(
            api_endpoint,
            params=params,
            headers=headers
        ) as response:
            data = await response.json()
            flights = data['data']

            # confirm every flight
            flights_copy = [
                await confirm_flight(session, flight)
                for flight in flights
            ]

            # filter not confirmed flights
            flights_copy = [
                flight
                for flight in flights_copy
                if flight is not None
            ]

            # sorting flights by price
            data['data'] = sorted(
                flights_copy,
                key=lambda x: x['flights_price']
            )

            await connection.set(f"{from_city}-{to_city}", json.dumps(data))


# @aiocron.crontab('0 0 0 * *')
async def autoupdate_redis():
    connection = (await RedisConnection()).connection

    # setup today and day in a month
    date_from = date.today()
    date_to = date_from + relativedelta(months=+1)

    # formatting for api
    date_from = f"{date_from.day}/{date_from.month}/{date_from.year}"
    date_to = f"{date_to.day}/{date_to.month}/{date_to.year}"

    # creating task for each direction
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

    # running tasks
    await asyncio.gather(*update_tasks)


if __name__ == '__main__':
    asyncio.run(autoupdate_redis())
