from invoke import Collection

from tasks.changelog_check import changelog_check
from tasks.docker import namespace as docker
from tasks.docs import namespace as docs
from tasks.lint import lint
from tasks.release import build, release
from tasks.run import run
from tasks.test import coverage, test
from tasks.typecheck import typecheck
from tasks.verify import verify

namespace = Collection(
    build,
    changelog_check,
    coverage,
    docker,
    docs,
    lint,
    release,
    run,
    test,
    typecheck,
    verify,
)
