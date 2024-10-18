# RoboNerva

[![Ruff](https://github.com/nerva-project/RoboNerva/actions/workflows/ruff.yml/badge.svg)](https://github.com/nerva-project/RoboNerva/actions/workflows/ruff.yml)
[![License](https://img.shields.io/github/license/nerva-project/RoboNerva)](LICENSE)

## Table of Contents

- [About](#about)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running](#running)
- [License](#license)

## About

RoboNerva is a Discord bot for the Nerva community. It is built using
the [discord.py](https://pypi.org/project/discord.py/) library and [MongoDB](https://www.mongodb.com/) for data storage.

## Prerequisites

- Git
- Python >= 3.8
- [`uv` package manager](https://docs.astral.sh/uv/getting-started/installation/)
- [MongoDB Atlas](https://www.mongodb.com/products/platform/atlas-database) or any other MongoDB instance

## Installation

1. Clone the repository.

   ```shell
   git clone https://github.com/nerva-project/RoboNerva.git
   ```

2. Switch to the project directory.

   ```shell
   cd RoboNerva
   ```

3. Install the dependencies.

   ```shell
   uv sync --no-dev
   ```
   
4. (Optional) Set up a development environment by installing the development dependencies and extras.

   ```shell
   uv sync --all-extras
   ```

## Configuration

Copy the [`config.example.py`](config.example.py) file to `config.py` and update the variables.

## Running

```shell
uv run launcher.py
```

## License

[GNU General Public License v3.0](LICENSE)

Copyright &copy; 2024 [Sayan "Sn1F3rt" Bhattacharyya](https://sn1f3rt.dev), [The Nerva Project](https://nerva.one)
