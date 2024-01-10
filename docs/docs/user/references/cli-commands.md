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
* `generate`: Generate enriched pipeline representation
* `manifest`: Render final resource representation
* `reset`: Reset pipeline steps
* `schema`: Generate JSON schema.

## `kpops clean`

Clean pipeline steps

**Usage**:

```console
$ kpops clean [OPTIONS] PIPELINE_PATH
```

**Arguments**:

* `PIPELINE_PATH`: Path to YAML with pipeline definition  [env var: KPOPS_PIPELINE_PATH;required]

**Options**:

* `--dotenv FILE`: Path to dotenv file. Multiple files can be provided. The files will be loaded in order, with each file overriding the previous one.  [env var: KPOPS_DOTENV_PATH]
* `--defaults DIRECTORY`: Path to defaults folder  [env var: KPOPS_DEFAULT_PATH]
* `--config DIRECTORY`: Path to the dir containing config.yaml files  [env var: KPOPS_CONFIG_PATH; default: .]
* `--steps TEXT`: Comma separated list of steps to apply the command on  [env var: KPOPS_PIPELINE_STEPS]
* `--filter-type [include|exclude]`: Whether the --steps option should include/exclude the steps  [default: FilterType.INCLUDE]
* `--environment TEXT`: The environment you want to generate and deploy the pipeline to. Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development).   [env var: KPOPS_ENVIRONMENT]
* `--dry-run / --execute`: Whether to dry run the command or execute it  [default: dry-run]
* `--verbose / --no-verbose`: Enable verbose printing  [default: no-verbose]
* `--help`: Show this message and exit.

## `kpops deploy`

Deploy pipeline steps

**Usage**:

```console
$ kpops deploy [OPTIONS] PIPELINE_PATH
```

**Arguments**:

* `PIPELINE_PATH`: Path to YAML with pipeline definition  [env var: KPOPS_PIPELINE_PATH;required]

**Options**:

* `--dotenv FILE`: Path to dotenv file. Multiple files can be provided. The files will be loaded in order, with each file overriding the previous one.  [env var: KPOPS_DOTENV_PATH]
* `--defaults DIRECTORY`: Path to defaults folder  [env var: KPOPS_DEFAULT_PATH]
* `--config DIRECTORY`: Path to the dir containing config.yaml files  [env var: KPOPS_CONFIG_PATH; default: .]
* `--steps TEXT`: Comma separated list of steps to apply the command on  [env var: KPOPS_PIPELINE_STEPS]
* `--filter-type [include|exclude]`: Whether the --steps option should include/exclude the steps  [default: FilterType.INCLUDE]
* `--environment TEXT`: The environment you want to generate and deploy the pipeline to. Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development).   [env var: KPOPS_ENVIRONMENT]
* `--dry-run / --execute`: Whether to dry run the command or execute it  [default: dry-run]
* `--verbose / --no-verbose`: Enable verbose printing  [default: no-verbose]
* `--help`: Show this message and exit.

## `kpops destroy`

Destroy pipeline steps

**Usage**:

```console
$ kpops destroy [OPTIONS] PIPELINE_PATH
```

**Arguments**:

* `PIPELINE_PATH`: Path to YAML with pipeline definition  [env var: KPOPS_PIPELINE_PATH;required]

**Options**:

* `--dotenv FILE`: Path to dotenv file. Multiple files can be provided. The files will be loaded in order, with each file overriding the previous one.  [env var: KPOPS_DOTENV_PATH]
* `--defaults DIRECTORY`: Path to defaults folder  [env var: KPOPS_DEFAULT_PATH]
* `--config DIRECTORY`: Path to the dir containing config.yaml files  [env var: KPOPS_CONFIG_PATH; default: .]
* `--steps TEXT`: Comma separated list of steps to apply the command on  [env var: KPOPS_PIPELINE_STEPS]
* `--filter-type [include|exclude]`: Whether the --steps option should include/exclude the steps  [default: FilterType.INCLUDE]
* `--environment TEXT`: The environment you want to generate and deploy the pipeline to. Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development).   [env var: KPOPS_ENVIRONMENT]
* `--dry-run / --execute`: Whether to dry run the command or execute it  [default: dry-run]
* `--verbose / --no-verbose`: Enable verbose printing  [default: no-verbose]
* `--help`: Show this message and exit.

## `kpops generate`

Enrich pipeline steps with defaults. The enriched pipeline is used for all KPOps operations (deploy, destroy, ...).

**Usage**:

```console
$ kpops generate [OPTIONS] PIPELINE_PATH
```

**Arguments**:

* `PIPELINE_PATH`: Path to YAML with pipeline definition  [env var: KPOPS_PIPELINE_PATH;required]

**Options**:

* `--dotenv FILE`: Path to dotenv file. Multiple files can be provided. The files will be loaded in order, with each file overriding the previous one.  [env var: KPOPS_DOTENV_PATH]
* `--defaults DIRECTORY`: Path to defaults folder  [env var: KPOPS_DEFAULT_PATH]
* `--config DIRECTORY`: Path to the dir containing config.yaml files  [env var: KPOPS_CONFIG_PATH; default: .]
* `--output / --no-output`: Enable output printing  [default: output]
* `--steps TEXT`: Comma separated list of steps to apply the command on  [env var: KPOPS_PIPELINE_STEPS]
* `--filter-type [include|exclude]`: Whether the --steps option should include/exclude the steps  [default: FilterType.INCLUDE]
* `--environment TEXT`: The environment you want to generate and deploy the pipeline to. Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development).   [env var: KPOPS_ENVIRONMENT]
* `--verbose / --no-verbose`: Enable verbose printing  [default: no-verbose]
* `--help`: Show this message and exit.

## `kpops manifest`

In addition to generate, render final resource representation for each pipeline step, e.g. Kubernetes manifests.

**Usage**:

```console
$ kpops manifest [OPTIONS] PIPELINE_PATH
```

**Arguments**:

* `PIPELINE_PATH`: Path to YAML with pipeline definition  [env var: KPOPS_PIPELINE_PATH;required]

**Options**:

* `--dotenv FILE`: Path to dotenv file. Multiple files can be provided. The files will be loaded in order, with each file overriding the previous one.  [env var: KPOPS_DOTENV_PATH]
* `--defaults DIRECTORY`: Path to defaults folder  [env var: KPOPS_DEFAULT_PATH]
* `--config DIRECTORY`: Path to the dir containing config.yaml files  [env var: KPOPS_CONFIG_PATH; default: .]
* `--output / --no-output`: Enable output printing  [default: output]
* `--steps TEXT`: Comma separated list of steps to apply the command on  [env var: KPOPS_PIPELINE_STEPS]
* `--filter-type [include|exclude]`: Whether the --steps option should include/exclude the steps  [default: FilterType.INCLUDE]
* `--environment TEXT`: The environment you want to generate and deploy the pipeline to. Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development).   [env var: KPOPS_ENVIRONMENT]
* `--verbose / --no-verbose`: Enable verbose printing  [default: no-verbose]
* `--help`: Show this message and exit.

## `kpops reset`

Reset pipeline steps

**Usage**:

```console
$ kpops reset [OPTIONS] PIPELINE_PATH
```

**Arguments**:

* `PIPELINE_PATH`: Path to YAML with pipeline definition  [env var: KPOPS_PIPELINE_PATH;required]

**Options**:

* `--dotenv FILE`: Path to dotenv file. Multiple files can be provided. The files will be loaded in order, with each file overriding the previous one.  [env var: KPOPS_DOTENV_PATH]
* `--defaults DIRECTORY`: Path to defaults folder  [env var: KPOPS_DEFAULT_PATH]
* `--config DIRECTORY`: Path to the dir containing config.yaml files  [env var: KPOPS_CONFIG_PATH; default: .]
* `--steps TEXT`: Comma separated list of steps to apply the command on  [env var: KPOPS_PIPELINE_STEPS]
* `--filter-type [include|exclude]`: Whether the --steps option should include/exclude the steps  [default: FilterType.INCLUDE]
* `--environment TEXT`: The environment you want to generate and deploy the pipeline to. Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development).   [env var: KPOPS_ENVIRONMENT]
* `--dry-run / --execute`: Whether to dry run the command or execute it  [default: dry-run]
* `--verbose / --no-verbose`: Enable verbose printing  [default: no-verbose]
* `--help`: Show this message and exit.

## `kpops schema`

Generate JSON schema.

The schemas can be used to enable support for KPOps files in a text editor.

**Usage**:

```console
$ kpops schema [OPTIONS] SCOPE:{pipeline|defaults|config}
```

**Arguments**:

* `SCOPE:{pipeline|defaults|config}`: 
        Scope of the generated schema
        



        pipeline: Schema of PipelineComponents. Includes the built-in KPOps components by default. To include custom components, provide components module in config.
        



        config: Schema of KpopsConfig.  [required]

**Options**:

* `--config DIRECTORY`: Path to the dir containing config.yaml files  [env var: KPOPS_CONFIG_PATH; default: .]
* `--include-stock-components / --no-include-stock-components`: Include the built-in KPOps components.  [default: include-stock-components]
* `--help`: Show this message and exit.
