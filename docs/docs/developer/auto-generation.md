# Auto generation

Auto generation happens mostly with Git hooks. You can find the [`lefthook`](https://evilmartians.github.io/lefthook/) configuration [here](https://github.com/bakdata/kpops/blob/main/lefthook.yaml). These pre-commit hooks call different [Python scripts](https://github.com/bakdata/kpops/tree/main/hooks) to auto generate code for the documentation.

## Generation scripts and their respective files

### [Documentation](https://github.com/bakdata/kpops/tree/main/hooks/gen_docs)

#### [Variables](https://github.com/bakdata/kpops/tree/main/docs/docs/resources/variables)

- `cli_env_vars.env` -- All CLI environment variables in a `dotenv` file.
- `cli_env_vars.md` -- All CLI environment variables in a table.
- `config_env_vars.env` -- Almost all pipeline config environment variables in a `dotenv` file. The script checks for each field in [`KpopsConfig`](https://github.com/bakdata/kpops/blob/main/kpops/cli/kpops_config.py) whether it has an `env` attribute defined. The script is currently unable to visit the classes of fields like `topic_name_config`, hence any environment variables defined there would remain unknown to it.
- `config_env_vars.env` -- Almost all pipeline config environment variables in a table.
- `variable_substitution.yaml` -- A copy of `./tests/pipeline/resources/component-type-substitution/pipeline.yaml` used as an example of substitution.

#### [CLI commands](../user/references/cli-commands.md)

Generated by `typer-cli` from the code in [`main.py`](https://github.com/bakdata/kpops/blob/main/kpops/cli/main.py). It is called with Python's `subprocess` module.

#### [Pipeline](https://github.com/bakdata/kpops/tree/main/docs/docs/resources/pipeline-components) and [defaults](https://github.com/bakdata/kpops/tree/main/docs/docs/resources/pipeline-defaults) example definitions

Generates example `pipeline.yaml` and `defaults.yaml` for each individual component, stores them and also concatenates them into 1 big pipeline definition and 1 big pipeline defaults definition.

User input

- `headers/*\.yaml` -- The top of each example. Includes a description comment, `type` and `name`. The headers for `pipeline.yaml` reside in the `pipeline-components` dir and the `defaults.yaml` headers reside in the `pipeline-defaults` dir. The names of the files must be equal to the respective component `type`.
- `sections/*\.yaml` -- Each YAML file contains a single section (component attribute) definition. The intention is to keep the minimal set of definitions there from which any component definition can be built. The names of the files must be equal to the respective component `type` and the attribute name. The sections are used for both `defaults.yaml` and `pipeline.yaml` generation and reside in the `pipeline-components` dir.

Generated

- `pipeline-components/dependencies/*`
  Cached information about KPOps components
  - `pipeline_component_dependencies.yaml` -- Specifies per component which files in the `sections` dir should be used for the `pipeline.yaml` generation.
  - `defaults_pipeline_component_dependencies.yaml` -- Specifies per component which files in the `sections` dir should be used for the `defaults.yaml` generation.
  - `kpops_structure.yaml` -- Specifies the inheritance hierarchy of the components and what sections exist in each component.
- `pipeline-components/*\.yaml` -- All single-component pipeline definitions and one big (complete) `pipeline.yaml` that contains all of them.
- `pipeline-defaults/*\.yaml` -- All single-component defaults definitions and one big (complete) `defaults.yaml` that contains all of them.

### [Editor integration](https://github.com/bakdata/kpops/blob/main/hooks/gen_schema.py)

#### [Schemas](https://github.com/bakdata/kpops/tree/main/docs/docs/schema)

- [config.json](https://github.com/bakdata/kpops/blob/main/docs/docs/schema/config.json)
- [pipeline.json](https://github.com/bakdata/kpops/blob/main/docs/docs/schema/pipeline.json)
