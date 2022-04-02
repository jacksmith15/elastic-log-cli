from pathlib import Path

from invoke import Collection, task

from tasks.helpers import package, print_header

RELEASE_BRANCH = "main"

PACKAGE_FILE = str(Path(package.__file__).relative_to(Path(__file__).parent.parent.absolute()))


@task()
def build(ctx):
    """Build docker image."""
    print_header("Building image")
    ctx.run(f"docker build . --tag elastic-log-cli:{package.__version__}")


namespace = Collection("docker", build)
