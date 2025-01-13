# Render the documentation locally

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- [just 1.5.0+](https://github.com/casey/just)

## Serve the docs

1. Clone the repository
   ```sh
   git clone git@github.com:bakdata/kpops.git
   ```
2. Change directory to `kpops`.
3. Install the documentation dependencies and use `just` to serve the docs:
   ```sh
   just serve-docs
   ```
   Go to your browser and open [http://localhost:8000/](http://localhost:8000/).
