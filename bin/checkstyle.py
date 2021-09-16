#!/usr/bin/env python3

from pathlib import Path
from subprocess import run

import click

PROJ_ROOT = Path(__file__).parent.parent.absolute()


@click.command()
@click.option("-w", "--write", is_flag=True)
def main(write):
    if write:
        format_files()
    else:
        check_only()


def prettier(args, **kwargs):
    if run("which prettier", shell=True).returncode == 0:
        return run(
            [
                "prettier",
                f"--config={PROJ_ROOT/'.prettierrc.yml'}",
                f"--ignore-path={PROJ_ROOT/'.prettierignore'}",
                *args,
            ],
            **kwargs,
        )
    else:
        return run(["echo", "prettier is not installed."])


def check_only():
    procs = [
        run(["poetry", "run", "flake8", "--show-source", "."], cwd=PROJ_ROOT),
        run(["poetry", "run", "black", "--check", "."], cwd=PROJ_ROOT),
        run(["poetry", "run", "isort", "--check", "."], cwd=PROJ_ROOT),
        prettier(["--check", "."], cwd=PROJ_ROOT),
    ]
    error = False
    for p in procs:
        if p.returncode != 0:
            print(f"Issues found after running {p.args}.")
            error = True
    if error:
        exit("Issues found after running checkstyle. Run checkstyle -w to autofix.")


def format_files():
    run(
        [
            "poetry",
            "run",
            "autoflake",
            "-i",
            "--ignore-init-module-imports",
            "--remove-all-unused-imports",
            "-r",
            ".",
        ],
        cwd=PROJ_ROOT,
    )
    run(["poetry", "run", "isort", "."], cwd=PROJ_ROOT, check=True)
    run(["poetry", "run", "black", "."], cwd=PROJ_ROOT, check=True)
    prettier(["-w", "."], cwd=PROJ_ROOT, check=True)


if __name__ == "__main__":
    main()
