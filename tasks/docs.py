import re
from pathlib import Path

from invoke import Collection, task


@task()
def config(ctx):
    """Generates docs for CLI configuration from Settings class."""
    ctx.run("""settings-doc generate \
  --class elastic_log_cli.config.Settings \
  --output-format markdown \
  --update README.md \
  --between "<!-- generated env. vars. start -->" "<!-- generated env. vars. end -->" \
  --heading-offset 2
""")


@task()
def usage(ctx):
    """Generates docs for CLI usage from --help."""
    help_text = "\n".join(["```", ctx.run("elastic-logs --help", hide="stdout").stdout, "```"])
    path = Path("README.md")
    content = path.read_text()
    start, end = "<!-- generated usage start -->", "<!-- generated usage end -->"
    pattern = re.compile(f"({re.escape(start)}\n?).*(\n?{re.escape(end)})", re.DOTALL)

    new_content = pattern.sub(f"\\1{help_text}\n\\2", content, count=1)
    with open(path, "w", encoding="utf-8") as file:
        file.write(new_content)




@task(pre=[config, usage])
def all(ctx):
    """Run all doc generation commands."""
    del ctx


namespace = Collection("docs", all, config, usage)
