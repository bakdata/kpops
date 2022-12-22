# Render the documentation locally

## Prerequisites

- [just 1.5.0+](https://github.com/casey/just)
- [Poetry (Version 1.2.2+)](https://github.com/python-poetry/poetry)

## Serve the docs

1. Clone the repository
   ```shell
   git clone git@github.com:bakdata/kpops.git
   ```
2. Change directory to `kops`.
3. Install the documentation dependencies and use `just` to serve the docs:
   ```shell
   poetry install --with docs && \
   just serve-docs
   ```
   Go to your browser and open [http://localhost:8000/](http://localhost:8000/).
