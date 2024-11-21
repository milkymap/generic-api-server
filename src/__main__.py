import click 
import asyncio 

from dotenv import load_dotenv

from src.api.app import APPServer
from src.settings.app import AppSettings
from src.settings.manager import ManagerSettings

from src.backend import Embedding, start_backend

@click.group()
@click.pass_context
def handler(ctx:click.core.Context):
    ctx.ensure_object(dict)
    ctx.obj['app_settings'] = AppSettings()
    ctx.obj['manager_settings'] = ManagerSettings()

@handler.command()
@click.pass_context
def launch_server(ctx:click.core.Context):
    app_settings:AppSettings = ctx.obj['app_settings']
    manager_settings:ManagerSettings = ctx.obj['manager_settings']
    async def main():
        server = APPServer(app_settings=app_settings) 
        await server.listen(manager_settings=manager_settings)

    backend_process = start_backend(
        nb_workers=1,
        frontend_addr='ipc:///tmp/frontend.worker.ipc',
        backend_addr='ipc:///tmp/backend.worker.ipc',
        strategy_cls=Embedding,
        model_name='all-mini-lm-v2',
        device='cuda:0'
    )
    asyncio.run(main=main())
    backend_process.join()

if __name__ == '__main__':
    load_dotenv()
    handler(obj={})
