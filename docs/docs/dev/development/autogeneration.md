# Autogeneration

## Documentation

Part of the documentation is generated automatically by the `pre-commit` hooks in `/kpops/hooks`.

### Generation scripts and their respective files

#### `gen_docs.py`

**`./kpops/docs/docs/resources/variables/*`**

- `cli_env_vars.env` -- All CLI environment variables in a `dotenv` file.
- `cli_env_vars.md` -- All CLI environment variables in a table.
- `config_env_vars.env` -- Almost all pipeline config environment variables in a `dotenv` file. The script checks for each field in `PipelineConfig` from `./kpops/kpops/cli/pipeline_config.py` whether it has an `env` attribute defined. The script is currently unable to visit the classes of fields like `topic_name_config`, hence any environment variables defined there would remain unknown to it.
- `config_env_vars.env` -- Almost all pipeline config environment variables in a table.
- `variable_substitution.yaml` -- A copy of `./tests/pipeline/resources/component-type-substitution/pipeline.yaml` used as an example of substition.

#### `gen_schema.py`

**`./kpops/docs/docs/schema/*`**

- `config.json`
- `pipeline.json`
