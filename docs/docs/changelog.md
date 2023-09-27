# Changelog

## [2.0.1](https://github.com/bakdata/kpops/releases/tag/2.0.1) - [2023-08-22]

**🐛 Fixes**

- Fix optional flags in GitHub action - [#334](https://github.com/bakdata/kpops/pull/334)

## [2.0.0](https://github.com/bakdata/kpops/releases/tag/2.0.0) - [2023-08-17]

**🏗️ Breaking changes**

- Remove camel case conversion of internal models - [#308](https://github.com/bakdata/kpops/pull/308)

- Derive component type automatically from class name - [#309](https://github.com/bakdata/kpops/pull/309)

- Refactor input/output types - [#232](https://github.com/bakdata/kpops/pull/232)

- v2 - [#321](https://github.com/bakdata/kpops/pull/321)

**🚀 Features**

- Automatically support schema generation for custom components - [#307](https://github.com/bakdata/kpops/pull/307)

- Derive component type automatically from class name - [#309](https://github.com/bakdata/kpops/pull/309)

**🏭 Refactor**

- Refactor input/output types - [#232](https://github.com/bakdata/kpops/pull/232)

**📝 Documentation**

- Fix editor integration example in docs - [#273](https://github.com/bakdata/kpops/pull/273)

## [1.7.2](https://github.com/bakdata/kpops/releases/tag/1.7.2) - [2023-08-16]

**🏭 Refactor**

- Refactor Kafka Connect handler - [#322](https://github.com/bakdata/kpops/pull/322)

**📝 Documentation**

- Add KPOps Runner GitHub Action to the documentation - [#325](https://github.com/bakdata/kpops/pull/325)

- Remove `:type` and `:rtype` from docstrings - [#324](https://github.com/bakdata/kpops/pull/324)

## [1.7.1](https://github.com/bakdata/kpops/releases/tag/1.7.1) - [2023-08-15]

**📝 Documentation**

- Modularize and autogenerate examples for the documentation - [#267](https://github.com/bakdata/kpops/pull/267)

- Update the variable documentation - [#266](https://github.com/bakdata/kpops/pull/266)

## [1.7.0](https://github.com/bakdata/kpops/releases/tag/1.7.0) - [2023-08-15]

**🚀 Features**

- Add flag to exclude pipeline steps - [#300](https://github.com/bakdata/kpops/pull/300)

## [1.6.0](https://github.com/bakdata/kpops/releases/tag/1.6.0) - [2023-08-10]

**🏭 Refactor**

- Refactor handling of Helm flags - [#319](https://github.com/bakdata/kpops/pull/319)

## [1.5.0](https://github.com/bakdata/kpops/releases/tag/1.5.0) - [2023-08-10]

**🚀 Features**

- Refactor Helm wrapper and add `--set-file` flag - [#311](https://github.com/bakdata/kpops/pull/311)

**🏭 Refactor**

- Refactor Helm wrapper and add `--set-file` flag - [#311](https://github.com/bakdata/kpops/pull/311)

- Set default for ToSection topics - [#313](https://github.com/bakdata/kpops/pull/313)

- Annotate types for ToSection models mapping - [#315](https://github.com/bakdata/kpops/pull/315)

**🌀 Miscellaneous**

- Check Poetry lock file consistency - [#316](https://github.com/bakdata/kpops/pull/316)

## [1.4.0](https://github.com/bakdata/kpops/releases/tag/1.4.0) - [2023-08-02]

**🐛 Fixes**

- Validate unique step names - [#292](https://github.com/bakdata/kpops/pull/292)

**🏭 Refactor**

- Order PipelineComponent fields - [#290](https://github.com/bakdata/kpops/pull/290)

- Migrate requests to httpx - [#302](https://github.com/bakdata/kpops/pull/302)

- Refactor CLI using dtyper - [#306](https://github.com/bakdata/kpops/pull/306)

**🌀 Miscellaneous**

- Update Black - [#294](https://github.com/bakdata/kpops/pull/294)

- Fix vulnerability in mkdocs-material - [#295](https://github.com/bakdata/kpops/pull/295)

- Move breaking changes section upper in the change log config - [#287](https://github.com/bakdata/kpops/pull/287)

## [1.3.2](https://github.com/bakdata/kpops/releases/tag/1.3.2) - [2023-07-13]

**🐛 Fixes**

- Exclude Helm tests from dry-run diff - [#293](https://github.com/bakdata/kpops/pull/293)

## [1.3.1](https://github.com/bakdata/kpops/releases/tag/1.3.1) - [2023-07-11]

**🏭 Refactor**

- Remove workaround for pipeline steps - [#276](https://github.com/bakdata/kpops/pull/276)

**🌀 Miscellaneous**

- Update codeowners - [#281](https://github.com/bakdata/kpops/pull/281)

- Reactivate Windows CI - [#255](https://github.com/bakdata/kpops/pull/255)

- Downgrade Poetry version on the Windows CI pipeline - [#286](https://github.com/bakdata/kpops/pull/286)

- Set ANSI theme for output of `kpops generate` - [#289](https://github.com/bakdata/kpops/pull/289)

## [1.3.0](https://github.com/bakdata/kpops/releases/tag/1.3.0) - [2023-07-07]

**🏭 Refactor**

- Plural broker field in pipeline config - [#278](https://github.com/bakdata/kpops/pull/278)

**📝 Documentation**

- Update KPOps runner readme for dev versions - [#279](https://github.com/bakdata/kpops/pull/279)

**🏗️ Breaking changes**

- Plural broker field in pipeline config - [#278](https://github.com/bakdata/kpops/pull/278)

**🌀 Miscellaneous**

- Add breaking changes section to change log config - [#280](https://github.com/bakdata/kpops/pull/280)

## [1.2.4](https://github.com/bakdata/kpops/releases/tag/1.2.4) - [2023-06-27]

**🌀 Miscellaneous**

- Update changelog action to contain miscellaneous PRs - [#269](https://github.com/bakdata/kpops/pull/269)

## [1.2.3](https://github.com/bakdata/kpops/releases/tag/1.2.3) - [2023-06-22]

**🐛 Fixes**

- Refactor custom component validation & hide field from kpops output - [#265](https://github.com/bakdata/kpops/pull/265)

**🏭 Refactor**

- Refactor custom component validation & hide field from kpops output - [#265](https://github.com/bakdata/kpops/pull/265)

**🌀 Miscellaneous**

## [1.2.2](https://github.com/bakdata/kpops/releases/tag/1.2.2) - [2023-06-21]

**🌀 Miscellaneous**

- Create workflow to lint CI - [#260](https://github.com/bakdata/kpops/pull/260)

- Fix update docs when releasing - [#261](https://github.com/bakdata/kpops/pull/261)

- Rename change log message for uncategorized issues - [#262](https://github.com/bakdata/kpops/pull/262)

## [1.2.1](https://github.com/bakdata/kpops/releases/tag/1.2.1) - [2023-06-21]

<summary>Uncategorized</summary>

- Fix update docs in release workflow - [#258](https://github.com/bakdata/kpops/pull/258)

## [1.2.0](https://github.com/bakdata/kpops/releases/tag/1.2.0) - [2023-06-21]

**🚀 Features**

- Add `helm repo update <repo-name>` for Helm >3.7 - [#239](https://github.com/bakdata/kpops/pull/239)

**🐛 Fixes**

- add --namespace option to Helm template command - [#237](https://github.com/bakdata/kpops/pull/237)

- Add missing type annotation for Pydantic attributes - [#238](https://github.com/bakdata/kpops/pull/238)

- Fix helm version check - [#242](https://github.com/bakdata/kpops/pull/242)

- Fix Helm Version Check - [#244](https://github.com/bakdata/kpops/pull/244)

- Fix import from external module - [#256](https://github.com/bakdata/kpops/pull/256)

**🏭 Refactor**

- Remove enable option from helm diff - [#235](https://github.com/bakdata/kpops/pull/235)

- Refactor variable substitution - [#198](https://github.com/bakdata/kpops/pull/198)

<summary>Uncategorized</summary>

- Add background to docs home page - [#236](https://github.com/bakdata/kpops/pull/236)

- Update Poetry version in CI - [#247](https://github.com/bakdata/kpops/pull/247)

- Add pip cache in KPOps runner action - [#249](https://github.com/bakdata/kpops/pull/249)

- Check types using Pyright - [#251](https://github.com/bakdata/kpops/pull/251)

- Remove MyPy - [#252](https://github.com/bakdata/kpops/pull/252)

- Disable broken Windows CI temporarily - [#253](https://github.com/bakdata/kpops/pull/253)

- Update release and publish workflows - [#254](https://github.com/bakdata/kpops/pull/254)

- Fix release & publish workflows - [#257](https://github.com/bakdata/kpops/pull/257)
