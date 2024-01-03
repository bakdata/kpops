# Environment variables

Environment variables can be set by using the [export](https://www.unix.com/man-page/linux/1/export/){target=_blank} command in Linux or the [set](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/set_1){target=_blank} command in Windows.

<!-- dprint-ignore-start -->

!!! tip "dotenv files"

    KPOps currently supports `.env` files only for variables related to the [config](../config.md). Full support for `.env` files is on the [roadmap](https://github.com/bakdata/kpops/issues/20). One of the possible ways to use one and export the contents manually is with the following command: `#!sh export $(xargs < .env)`. This would work in `bash` suppose there are no spaces inside the values.

<!-- dprint-ignore-end -->

## Config

--8<--
./docs/resources/variables/config_env_vars.md
--8<--

<!-- dprint-ignore-start -->

??? example "config_env_vars.env"

    ```py title="Exhaustive list of all config-related environment variables"
    --8<--
    ./docs/resources/variables/config_env_vars.env
    --8<--
    ```

<!-- dprint-ignore-end -->

## CLI

--8<--
./docs/resources/variables/cli_env_vars.md
--8<--

<!-- dprint-ignore-start -->

??? example "cli_env_vars.env"

    ```py title="Exhaustive list of all cli-related environment variables"
    --8<--
    ./docs/resources/variables/cli_env_vars.env
    --8<--
    ```

<!-- dprint-ignore-end -->
