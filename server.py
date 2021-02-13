from aiohttp import web
import aiohttp_jinja2
import jinja2
import aioreloader
import json
from pathlib import Path
from autoupdate import autoupdate_redis
from autoupdate import (
    RedisConnection, 
    directions, locations
)


@aiohttp_jinja2.template('index.html')
async def index(request: web.Request) -> web.Response:
    return {}

# /api/flights?from={dir}&to={dir}
# /api/flight_detail/{flight}


async def api_flights(request: web.Request) -> web.Response:
    try: 
        from_city = request.query['from_city']
        if from_city not in locations:
            raise ValueError
    except KeyError:
        return web.Response(status=500, body=json.dumps({
            'status' : 'error',
            'data' : {
                'from_city' : 'Parameter from_city is a required field, but it was not given.'
            }
        }))
    except ValueError:
        return web.Response(status=500, body=json.dumps({
            'status' : 'error',
            'data' : {
                'from_city' : f'Not recognized location: `{from_city}`'
            }
        }))


    try: 
        to_city = request.query['to_city']
        if to_city not in locations:
            raise ValueError
    except KeyError:
        return web.Response(status=500, body=json.dumps({
            'status' : 'error',
            'data' : {
                'to_city' : 'Parameter to_city is a required field, but it was not given.'
            }
        }))
    except ValueError:
        return web.Response(status=500, body=json.dumps({
            'status' : 'error',
            'data' : {
                'to_city' : f'Not recognized location: `{to_city}`'
            }
        }))

    direction = f"{from_city}-{to_city}"

    if direction not in directions:
        return web.Response(status=500, body=json.dumps({
            'status' : 'error',
            'data' : {
                'message' : f'There are no flights between these locations: `{from_city}`, `{to_city}`'
            }
        }))

    redis_con = (await RedisConnection()).connection
    data = {
        'status' : 'success',
        'data' : (await redis_con.get(direction)).decode('utf-8')
    }
    
    return web.Response(status=200, body=json.dumps(data))


app = web.Application()
app.router.add_get('/', index)
app.router.add_post('/api/flights', api_flights)


templates_path = str(Path(__file__).resolve().parent) + '/templates'
aiohttp_jinja2.setup(
    app, 
    loader=jinja2.FileSystemLoader(templates_path)
)


if __name__ == '__main__':
    aioreloader.start()
    autoupdate_redis.start()
    web.run_app(app, host='localhost')