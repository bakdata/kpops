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

* `init`: Initialize a new KPOps project.
* `generate`: Generate enriched pipeline representation
* `deploy`: Deploy pipeline steps
* `destroy`: Destroy pipeline steps
* `reset`: Reset pipeline steps
* `clean`: Clean pipeline steps
* `schema`: Generate JSON schema.

## `kpops init`

Initialize a new KPOps project.

**Usage**:

```console
$ kpops init [OPTIONS] PATH
```

**Arguments**:

* `PATH`: Path for a new KPOps project. It should lead to an empty (or non-existent) directory. The part of the path that doesn&#x27;t exist will be created.  [required]

**Options**:

* `--config-include-optional / --no-config-include-optional`: Whether to include non-required settings in the generated &#x27;config.yaml&#x27;  [default: no-config-include-optional]
* `--help`: Show this message and exit.

## `kpops generate`

Enrich pipeline steps with defaults. The enriched pipeline is used for all KPOps operations (deploy, destroy, ...).

**Usage**:

```console
$ kpops generate [OPTIONS] PIPELINE_PATHS...
```

**Arguments**:

* `PIPELINE_PATHS...`: Paths to dir containing &#x27;pipeline.yaml&#x27; or files named &#x27;pipeline.yaml&#x27;.  [env var: KPOPS_PIPELINE_PATHS; required]

**Options**:

* `--dotenv FILE`: Path to dotenv file. Multiple files can be provided. The files will be loaded in order, with each file overriding the previous one.  [env var: KPOPS_DOTENV_PATH]
* `--config DIRECTORY`: Path to the dir containing config.yaml files  [env var: KPOPS_CONFIG_PATH; default: .]
* `--steps TEXT`: Comma separated list of steps to apply the command on  [env var: KPOPS_PIPELINE_STEPS]
* `--filter-type [include|exclude]`: Whether the --steps option should include/exclude the steps  [default: include]
* `--environment TEXT`: The environment you want to generate and deploy the pipeline to. Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development).   [env var: KPOPS_ENVIRONMENT]
* `--verbose / --no-verbose`: Enable verbose printing  [default: no-verbose]
* `--help`: Show this message and exit.

## `kpops deploy`

Deploy pipeline steps

**Usage**:

```console
$ kpops deploy [OPTIONS] PIPELINE_PATHS...
```

**Arguments**:

* `PIPELINE_PATHS...`: Paths to dir containing &#x27;pipeline.yaml&#x27; or files named &#x27;pipeline.yaml&#x27;.  [env var: KPOPS_PIPELINE_PATHS; required]

**Options**:

* `--dotenv FILE`: Path to dotenv file. Multiple files can be provided. The files will be loaded in order, with each file overriding the previous one.  [env var: KPOPS_DOTENV_PATH]
* `--config DIRECTORY`: Path to the dir containing config.yaml files  [env var: KPOPS_CONFIG_PATH; default: .]
* `--steps TEXT`: Comma separated list of steps to apply the command on  [env var: KPOPS_PIPELINE_STEPS]
* `--filter-type [include|exclude]`: Whether the --steps option should include/exclude the steps  [default: include]
* `--environment TEXT`: The environment you want to generate and deploy the pipeline to. Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development).   [env var: KPOPS_ENVIRONMENT]
* `--dry-run / --execute`: Whether to dry run the command or execute it  [default: dry-run]
* `--verbose / --no-verbose`: Enable verbose printing  [default: no-verbose]
* `--parallel / --no-parallel`: Enable or disable parallel execution of pipeline steps. If enabled, multiple steps can be processed concurrently. If disabled, steps will be processed sequentially.  [default: no-parallel]
* `--operation-mode [argo|manifest|managed]`: How KPOps should operate.  [env var: KPOPS_OPERATION_MODE; default: managed]
* `--help`: Show this message and exit.

## `kpops destroy`

Destroy pipeline steps

**Usage**:

```console
$ kpops destroy [OPTIONS] PIPELINE_PATHS...
```

**Arguments**:

* `PIPELINE_PATHS...`: Paths to dir containing &#x27;pipeline.yaml&#x27; or files named &#x27;pipeline.yaml&#x27;.  [env var: KPOPS_PIPELINE_PATHS; required]

**Options**:

* `--dotenv FILE`: Path to dotenv file. Multiple files can be provided. The files will be loaded in order, with each file overriding the previous one.  [env var: KPOPS_DOTENV_PATH]
* `--config DIRECTORY`: Path to the dir containing config.yaml files  [env var: KPOPS_CONFIG_PATH; default: .]
* `--steps TEXT`: Comma separated list of steps to apply the command on  [env var: KPOPS_PIPELINE_STEPS]
* `--filter-type [include|exclude]`: Whether the --steps option should include/exclude the steps  [default: include]
* `--environment TEXT`: The environment you want to generate and deploy the pipeline to. Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development).   [env var: KPOPS_ENVIRONMENT]
* `--dry-run / --execute`: Whether to dry run the command or execute it  [default: dry-run]
* `--verbose / --no-verbose`: Enable verbose printing  [default: no-verbose]
* `--parallel / --no-parallel`: Enable or disable parallel execution of pipeline steps. If enabled, multiple steps can be processed concurrently. If disabled, steps will be processed sequentially.  [default: no-parallel]
* `--operation-mode [argo|manifest|managed]`: How KPOps should operate.  [env var: KPOPS_OPERATION_MODE; default: managed]
* `--help`: Show this message and exit.

## `kpops reset`

Reset pipeline steps

**Usage**:

```console
$ kpops reset [OPTIONS] PIPELINE_PATHS...
```

**Arguments**:

* `PIPELINE_PATHS...`: Paths to dir containing &#x27;pipeline.yaml&#x27; or files named &#x27;pipeline.yaml&#x27;.  [env var: KPOPS_PIPELINE_PATHS; required]

**Options**:

* `--dotenv FILE`: Path to dotenv file. Multiple files can be provided. The files will be loaded in order, with each file overriding the previous one.  [env var: KPOPS_DOTENV_PATH]
* `--config DIRECTORY`: Path to the dir containing config.yaml files  [env var: KPOPS_CONFIG_PATH; default: .]
* `--steps TEXT`: Comma separated list of steps to apply the command on  [env var: KPOPS_PIPELINE_STEPS]
* `--filter-type [include|exclude]`: Whether the --steps option should include/exclude the steps  [default: include]
* `--environment TEXT`: The environment you want to generate and deploy the pipeline to. Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development).   [env var: KPOPS_ENVIRONMENT]
* `--dry-run / --execute`: Whether to dry run the command or execute it  [default: dry-run]
* `--verbose / --no-verbose`: Enable verbose printing  [default: no-verbose]
* `--parallel / --no-parallel`: Enable or disable parallel execution of pipeline steps. If enabled, multiple steps can be processed concurrently. If disabled, steps will be processed sequentially.  [default: no-parallel]
* `--operation-mode [argo|manifest|managed]`: How KPOps should operate.  [env var: KPOPS_OPERATION_MODE; default: managed]
* `--help`: Show this message and exit.

## `kpops clean`

Clean pipeline steps

**Usage**:

```console
$ kpops clean [OPTIONS] PIPELINE_PATHS...
```

**Arguments**:

* `PIPELINE_PATHS...`: Paths to dir containing &#x27;pipeline.yaml&#x27; or files named &#x27;pipeline.yaml&#x27;.  [env var: KPOPS_PIPELINE_PATHS; required]

**Options**:

* `--dotenv FILE`: Path to dotenv file. Multiple files can be provided. The files will be loaded in order, with each file overriding the previous one.  [env var: KPOPS_DOTENV_PATH]
* `--config DIRECTORY`: Path to the dir containing config.yaml files  [env var: KPOPS_CONFIG_PATH; default: .]
* `--steps TEXT`: Comma separated list of steps to apply the command on  [env var: KPOPS_PIPELINE_STEPS]
* `--filter-type [include|exclude]`: Whether the --steps option should include/exclude the steps  [default: include]
* `--environment TEXT`: The environment you want to generate and deploy the pipeline to. Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development).   [env var: KPOPS_ENVIRONMENT]
* `--dry-run / --execute`: Whether to dry run the command or execute it  [default: dry-run]
* `--verbose / --no-verbose`: Enable verbose printing  [default: no-verbose]
* `--parallel / --no-parallel`: Enable or disable parallel execution of pipeline steps. If enabled, multiple steps can be processed concurrently. If disabled, steps will be processed sequentially.  [default: no-parallel]
* `--operation-mode [argo|manifest|managed]`: How KPOps should operate.  [env var: KPOPS_OPERATION_MODE; default: managed]
* `--help`: Show this message and exit.

## `kpops schema`

Generate JSON schema.

The schemas can be used to enable support for KPOps files in a text editor.

**Usage**:

```console
$ kpops schema [OPTIONS] SCOPE:{pipeline|defaults|config}
```

**Arguments**:

* `SCOPE:{pipeline|defaults|config}`: Scope of the generated schema
        



        - pipeline: Schema of PipelineComponents for KPOps pipeline.yaml
        


        - defaults: Schema of PipelineComponents for KPOps defaults.yaml
        


        - config: Schema for KPOps config.yaml  [required]

**Options**:

* `--help`: Show this message and exit.
