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
    kwargs["check"] = True
    return run(
        [
            "prettier",
            f"--config={PROJ_ROOT/'.prettierrc.yml'}",
            f"--ignore-path={PROJ_ROOT/'.prettierignore'}",
            *args,
        ],
        **kwargs,
    )


def check_only():
    procs = [
        run(["flake8", "--show-source", PROJ_ROOT]),
        run(["black", "--check", PROJ_ROOT]),
        run(["isort", "--check", PROJ_ROOT]),
        prettier(["--check", PROJ_ROOT]),
    ]
    error = False
    for p in procs:
        if p.returncode != 0:
            print(f"Issues found after running {p.args}.")
            error = True
    if error:
        exit("Issues found after running checkstyle.")


def format_files():
    run(
        [
            "autoflake",
            "-i",
            "--ignore-init-module-imports",
            "--remove-all-unused-imports",
            "-r",
            ".",
        ],
        cwd=PROJ_ROOT,
    )
    run(["isort", "."], cwd=PROJ_ROOT, check=True)
    run(["black", "."], cwd=PROJ_ROOT)
    prettier(["-w", "."], cwd=PROJ_ROOT)


if __name__ == "__main__":
    main()
