#!/usr/bin/env python3

from pathlib import Path
from subprocess import CalledProcessError, run

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
    run(
        [
            "prettier",
            f"--config={PROJ_ROOT/'.prettierrc.yml'}",
            f"--ignore-path={PROJ_ROOT/'.prettierignore'}",
            *args,
        ],
        **kwargs,
    )


def check_only():
    try:
        run(["flake8", "--show-source", "."], cwd=PROJ_ROOT, check=True)
        run(["black", "--check", "."], cwd=PROJ_ROOT, check=True)
        run(["isort", "--check", "."], cwd=PROJ_ROOT, check=True)
        prettier(["--check", "."], cwd=PROJ_ROOT, check=True)
    except CalledProcessError as expt:
        exit(f"Issues found after running {expt.cmd} in {PROJ_ROOT}.")


def format_files():
    run(["black", "."], cwd=PROJ_ROOT)
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
    prettier(["-w", "."], cwd=PROJ_ROOT)


if __name__ == "__main__":
    main()
