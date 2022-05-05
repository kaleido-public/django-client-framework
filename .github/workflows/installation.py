#!/usr/bin/env python3

from subprocess import run


def install_black() -> None:
    if run(["which", "black"]).returncode != 0:
        run(["pip3", "install", "black"])


def install_flake8() -> None:
    if run(["which", "flake8"]).returncode != 0:
        run(["pip3", "install", "flake8"])


def install_node() -> None:
    if run(["which", "node"]).returncode != 0:
        run(["apt-get", "-y", "install", "nodejs"])


def install_npm() -> None:
    if run(["which", "npm"]).returncode != 0:
        run(["apt-get", "-y", "install", "npm"])


def install_prettier() -> None:
    if run(["which", "prettier"]).returncode != 0:
        run(["npm", "-g", "install", "prettier"])


def install_poetry() -> None:
    if run(["which", "poetry"]).returncode != 0:
        run(["pip3", "install", "poetry"])


def install_dependencies() -> None:
    run(["poetry", "install"])


if __name__ == "__main__":
    install_black()
    install_flake8()
    install_node()
    install_npm()
    install_prettier()
    install_poetry()
    install_dependencies()
