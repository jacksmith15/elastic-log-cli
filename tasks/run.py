from pathlib import Path

from invoke import task
from invoke.exceptions import Exit
from termcolor import colored

from tasks.helpers import package
from tasks.release import build

def env_file() -> str:
    path = Path(".env")
    if not path.exists():
        raise Exit(code=1, message=colored("No .env file defined. Have you copied from '.env.template'?", "red"))
    return str(path)


@task(pre=[build])
def run(ctx, command=None):
    tag = f"elastic-log-cli:{package.__version__}"
    if command:
        ctx.run(f"docker run -it --env-file {env_file()} --entrypoint {command} {tag}", pty=True)
    else:
        ctx.run(f"docker run --env-file {env_file()} {tag}")
