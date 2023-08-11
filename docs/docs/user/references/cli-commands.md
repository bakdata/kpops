# CLI Usage

**Usage**:

```console
$ kpops [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `-V, --version`: Print KPOps version
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `clean`: Clean pipeline steps
* `deploy`: Deploy pipeline steps
* `destroy`: Destroy pipeline steps
* `generate`: Enriches pipelines steps with defaults.
* `reset`: Reset pipeline steps
* `schema`: Generate json schema.

## `kpops clean`

Clean pipeline steps

**Usage**:

```console
$ kpops clean [OPTIONS] PIPELINE_PATH [COMPONENTS_MODULE]
```

**Arguments**:

* `PIPELINE_PATH`: Path to YAML with pipeline definition  [env var: KPOPS_PIPELINE_PATH;required]
* `[COMPONENTS_MODULE]`: Custom Python module containing your project-specific components

**Options**:

* `--pipeline-base-dir DIRECTORY`: Base directory to the pipelines (default is current working directory)  [env var: KPOPS_PIPELINE_BASE_DIR; default: .]
* `--defaults DIRECTORY`: Path to defaults folder  [env var: KPOPS_DEFAULT_PATH]
* `--config FILE`: Path to the config.yaml file  [env var: KPOPS_CONFIG_PATH; default: config.yaml]
* `--steps TEXT`: Comma separated list of steps to apply the command on  [env var: KPOPS_PIPELINE_STEPS]
* `--dry-run / --execute`: Whether to dry run the command or execute it  [default: dry-run]
* `--verbose / --no-verbose`: Enable verbose printing  [default: no-verbose]
* `--help`: Show this message and exit.

## `kpops deploy`

Deploy pipeline steps

**Usage**:

```console
$ kpops deploy [OPTIONS] PIPELINE_PATH [COMPONENTS_MODULE]
```

**Arguments**:

* `PIPELINE_PATH`: Path to YAML with pipeline definition  [env var: KPOPS_PIPELINE_PATH;required]
* `[COMPONENTS_MODULE]`: Custom Python module containing your project-specific components

**Options**:

* `--pipeline-base-dir DIRECTORY`: Base directory to the pipelines (default is current working directory)  [env var: KPOPS_PIPELINE_BASE_DIR; default: .]
* `--defaults DIRECTORY`: Path to defaults folder  [env var: KPOPS_DEFAULT_PATH]
* `--config FILE`: Path to the config.yaml file  [env var: KPOPS_CONFIG_PATH; default: config.yaml]
* `--dry-run / --execute`: Whether to dry run the command or execute it  [default: dry-run]
* `--verbose / --no-verbose`: Enable verbose printing  [default: no-verbose]
* `--steps TEXT`: Comma separated list of steps to apply the command on  [env var: KPOPS_PIPELINE_STEPS]
* `--help`: Show this message and exit.

## `kpops destroy`

Destroy pipeline steps

**Usage**:

```console
$ kpops destroy [OPTIONS] PIPELINE_PATH [COMPONENTS_MODULE]
```

**Arguments**:

* `PIPELINE_PATH`: Path to YAML with pipeline definition  [env var: KPOPS_PIPELINE_PATH;required]
* `[COMPONENTS_MODULE]`: Custom Python module containing your project-specific components

**Options**:

* `--pipeline-base-dir DIRECTORY`: Base directory to the pipelines (default is current working directory)  [env var: KPOPS_PIPELINE_BASE_DIR; default: .]
* `--defaults DIRECTORY`: Path to defaults folder  [env var: KPOPS_DEFAULT_PATH]
* `--config FILE`: Path to the config.yaml file  [env var: KPOPS_CONFIG_PATH; default: config.yaml]
* `--steps TEXT`: Comma separated list of steps to apply the command on  [env var: KPOPS_PIPELINE_STEPS]
* `--verbose / --no-verbose`: Enable verbose printing  [default: no-verbose]
* `--dry-run / --execute`: Whether to dry run the command or execute it  [default: dry-run]
* `--help`: Show this message and exit.

## `kpops generate`

Enriches pipelines steps with defaults. The output is used as input for the deploy/destroy/... commands.

**Usage**:

```console
$ kpops generate [OPTIONS] PIPELINE_PATH [COMPONENTS_MODULE]
```

**Arguments**:

* `PIPELINE_PATH`: Path to YAML with pipeline definition  [env var: KPOPS_PIPELINE_PATH;required]
* `[COMPONENTS_MODULE]`: Custom Python module containing your project-specific components

**Options**:

* `--pipeline-base-dir DIRECTORY`: Base directory to the pipelines (default is current working directory)  [env var: KPOPS_PIPELINE_BASE_DIR; default: .]
* `--defaults DIRECTORY`: Path to defaults folder  [env var: KPOPS_DEFAULT_PATH]
* `--config FILE`: Path to the config.yaml file  [env var: KPOPS_CONFIG_PATH; default: config.yaml]
* `--verbose / --no-verbose`: Enable verbose printing  [default: no-verbose]
* `--template / --no-template`: Run Helm template  [default: no-template]
* `--steps TEXT`: Comma separated list of steps to apply the command on  [env var: KPOPS_PIPELINE_STEPS]
* `--help`: Show this message and exit.

## `kpops reset`

Reset pipeline steps

**Usage**:

```console
$ kpops reset [OPTIONS] PIPELINE_PATH [COMPONENTS_MODULE]
```

**Arguments**:

* `PIPELINE_PATH`: Path to YAML with pipeline definition  [env var: KPOPS_PIPELINE_PATH;required]
* `[COMPONENTS_MODULE]`: Custom Python module containing your project-specific components

**Options**:

* `--pipeline-base-dir DIRECTORY`: Base directory to the pipelines (default is current working directory)  [env var: KPOPS_PIPELINE_BASE_DIR; default: .]
* `--defaults DIRECTORY`: Path to defaults folder  [env var: KPOPS_DEFAULT_PATH]
* `--config FILE`: Path to the config.yaml file  [env var: KPOPS_CONFIG_PATH; default: config.yaml]
* `--steps TEXT`: Comma separated list of steps to apply the command on  [env var: KPOPS_PIPELINE_STEPS]
* `--dry-run / --execute`: Whether to dry run the command or execute it  [default: dry-run]
* `--verbose / --no-verbose`: Enable verbose printing  [default: no-verbose]
* `--help`: Show this message and exit.

## `kpops schema`

Generate json schema.

The schemas can be used to enable support for kpops files in a text editor.

**Usage**:

```console
$ kpops schema [OPTIONS] SCOPE:{pipeline|config} [COMPONENTS_MODULE]
```

**Arguments**:

* `SCOPE:{pipeline|config}`: 
        Scope of the generated schema
        



        pipeline: Schema of PipelineComponents. Includes the built-in kpops components by default. To include custom components, provide [COMPONENTS_MODULES].
        



        config: Schema of PipelineConfig.  [required]
* `[COMPONENTS_MODULE]`: Custom Python module containing your project-specific components

**Options**:

* `--include-stock-components / --no-include-stock-components`: Include the built-in KPOps components.  [default: include-stock-components]
* `--help`: Show this message and exit.
