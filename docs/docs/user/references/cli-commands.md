# CLI usage

**Usage**:

```console
$ kpops [OPTIONS] COMMAND [ARGS]
```

**Options**:

- `--install-completion`: Install completion for the current shell.
- `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
- `--help`: Show this message and exit.

**Commands**:

- `clean`: Clean pipeline steps
- `deploy`: Deploy pipeline steps
- `destroy`: Destroy pipeline steps
- `generate`: Enriches pipelines steps with defaults. The output is used as input for the deploy/destroy/... commands.
- `reset`: Reset pipeline steps

## `clean`

Clean pipeline steps

**Usage**:

```console
$ kpops clean [OPTIONS] PIPELINE_PATH [COMPONENTS_MODULE]
```

**Arguments**:

- `pipeline_path FILE`: Path to YAML with pipeline definition [env var: KPOPS_PIPELINE_PATH] [default: None] [required]
- `components_module [COMPONENTS_MODULE]`: Custom Python module containing your project-specific components [default: None]

**Options**:

- `--pipeline-base-dir DIRECTORY`: Base directory to the pipelines (default is current working directory) [env var: KPOPS_PIPELINE_BASE_DIR] [default: .]
- `--defaults DIRECTORY`: Path to defaults folder [env var: KPOPS_DEFAULT_PATH] [default: defaults]
- `--config FILE`: Path to the config.yaml file [env var: KPOPS_CONFIG_PATH] [default: config.yaml]
- `--steps TEXT`: Comma separated list of steps to apply the command on [env var: KPOPS_PIPELINE_STEPS] [default: None]
- `--dry-run / --execute`: Whether to dry run the command or execute it [default: dry-run]
- `--verbose / --no-verbose`: [default: no-verbose]
- `--help`: Show this message and exit.

## `deploy`

Deploy pipeline steps

**Usage**:

```console
$ kpops deploy [OPTIONS] PIPELINE_PATH [COMPONENTS_MODULE]
```

**Arguments**:

- `pipeline_path FILE`: Path to YAML with pipeline definition [env var: KPOPS_PIPELINE_PATH] [default: None] [required]
- `components_module [COMPONENTS_MODULE]`: Custom Python module containing your project-specific components [default: None]

**Options**:

- `--pipeline-base-dir DIRECTORY`: Base directory to the pipelines (default is current working directory) [env var: KPOPS_PIPELINE_BASE_DIR] [default: .]
- `--defaults DIRECTORY`: Path to defaults folder [env var: KPOPS_DEFAULT_PATH] [default: defaults]
- `--config FILE`: Path to the config.yaml file [env var: KPOPS_CONFIG_PATH] [default: config.yaml]
- `--steps TEXT`: Comma separated list of steps to apply the command on [env var: KPOPS_PIPELINE_STEPS] [default: None]
- `--dry-run / --execute`: Whether to dry run the command or execute it [default: dry-run]
- `--verbose / --no-verbose`: [default: no-verbose]
- `--help`: Show this message and exit.

## `destroy`

Destroy pipeline steps

**Usage**:

```console
$ kpops destroy [OPTIONS] PIPELINE_PATH [COMPONENTS_MODULE]
```

**Arguments**:

- `pipeline_path FILE`: Path to YAML with pipeline definition [env var: KPOPS_PIPELINE_PATH] [default: None] [required]
- `components_module [COMPONENTS_MODULE]`: Custom Python module containing your project-specific components [default: None]

**Options**:

- `--pipeline-base-dir DIRECTORY`: Base directory to the pipelines (default is current working directory) [env var: KPOPS_PIPELINE_BASE_DIR] [default: .]
- `--defaults DIRECTORY`: Path to defaults folder [env var: KPOPS_DEFAULT_PATH] [default: defaults]
- `--config FILE`: Path to the config.yaml file [env var: KPOPS_CONFIG_PATH] [default: config.yaml]
- `--steps TEXT`: Comma separated list of steps to apply the command on [env var: KPOPS_PIPELINE_STEPS] [default: None]
- `--dry-run / --execute`: Whether to dry run the command or execute it [default: dry-run]
- `--verbose / --no-verbose`: [default: no-verbose]
- `--help`: Show this message and exit.

## `generate`

Enriches pipelines steps with defaults. The output is used as input for the deploy/destroy/... commands.

**Usage**:

```console
$ kpops generate [OPTIONS] PIPELINE_PATH [COMPONENTS_MODULE]
```

**Arguments**:

- `pipeline_path FILE`: Path to YAML with pipeline definition [env var: KPOPS_PIPELINE_PATH] [default: None] [required]
- `components_module [COMPONENTS_MODULE]`: Custom Python module containing your project-specific components [default: None]

**Options**:

- `--pipeline-base-dir DIRECTORY`: Base directory to the pipelines (default is current working directory) [env var: KPOPS_PIPELINE_BASE_DIR] [default: .]
- `--defaults DIRECTORY`: Path to defaults folder [env var: KPOPS_DEFAULT_PATH] [default: defaults]
- `--config FILE`: Path to the config.yaml file [env var: KPOPS_CONFIG_PATH] [default: config.yaml]
- `--print-yaml / --no-print-yaml`: Print enriched pipeline yaml definition [default: print-yaml]
- `--save / --no-save`: Save pipeline to yaml file [default: no-save]
- `--out-path PATH`: Path to file the yaml pipeline should be saved to [default: None]
- `--verbose / --no-verbose`: [default: no-verbose]
- `--help`: Show this message and exit.

## `reset`

Reset pipeline steps

**Usage**:

```console
$ reset [OPTIONS] PIPELINE_PATH COMPONENTS_MODULE
```

**Arguments**:

- `pipeline_path FILE`: Path to YAML with pipeline definition [env var: KPOPS_PIPELINE_PATH] [default: None] [required]
- `components_module [COMPONENTS_MODULE]`: Custom Python module containing your project-specific components [default: None]

**Options**:

- `--pipeline-base-dir DIRECTORY`: Base directory to the pipelines (default is current working directory) [env var: KPOPS_PIPELINE_BASE_DIR] [default: .]
- `--defaults DIRECTORY`: Path to defaults folder [env var: KPOPS_DEFAULT_PATH] [default: defaults]
- `--config FILE`: Path to the config.yaml file [env var: KPOPS_CONFIG_PATH] [default: config.yaml]
- `--steps TEXT`: Comma separated list of steps to apply the command on [env var: KPOPS_PIPELINE_STEPS] [default: None]
- `--dry-run / --execute`: Whether to dry run the command or execute it [default: dry-run]
- `--verbose / --no-verbose`: [default: no-verbose]
- `--help`: Show this message and exit.
