from aiohttp import web
import aiohttp_jinja2
import jinja2
import aioreloader
from pathlib import Path


@aiohttp_jinja2.template('index.html')
async def index(request: web.Request) -> web.Response:
    return {}


if __name__ == '__main__':
    app = web.Application()
    app.router.add_get('/', index)


    templates_path = str(Path(__file__).resolve().parent) + '/templates'
    aiohttp_jinja2.setup(
        app, 
        loader=jinja2.FileSystemLoader(templates_path)
    )

    aioreloader.start()
    web.run_app(app, host='localhost')