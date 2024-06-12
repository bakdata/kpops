# Changelog
## [6.0.1](https://github.com/bakdata/kpops/releases/tag/6.0.1) - Release Date: [2024-06-12]

### 🐛 Fixes

- Fix connector resetter offset topic - [#497](https://github.com/bakdata/kpops/pull/497)






## [6.0.0](https://github.com/bakdata/kpops/releases/tag/6.0.0) - Release Date: [2024-06-06]

### 🏗️ Breaking changes

- KPOps `6.0.0` - [#496](https://github.com/bakdata/kpops/pull/496)


### 🚀 Features

- KPOps `6.0.0` - [#496](https://github.com/bakdata/kpops/pull/496)


### 🏭 Refactor

- KPOps `6.0.0` - [#496](https://github.com/bakdata/kpops/pull/496)






## [5.1.1](https://github.com/bakdata/kpops/releases/tag/5.1.1) - Release Date: [2024-05-22]

### 🐛 Fixes

- Add YAML separator (---) to stdout - [#491](https://github.com/bakdata/kpops/pull/491)






## [5.1.0](https://github.com/bakdata/kpops/releases/tag/5.1.0) - Release Date: [2024-05-22]

### 🌀 Miscellaneous

- Add computed field for Helm release name and name override - [#490](https://github.com/bakdata/kpops/pull/490)






## [5.0.1](https://github.com/bakdata/kpops/releases/tag/5.0.1) - Release Date: [2024-05-15]

### 🐛 Fixes

- Fix missing await on Kubernetes API - [#488](https://github.com/bakdata/kpops/pull/488)






## [5.0.0](https://github.com/bakdata/kpops/releases/tag/5.0.0) - Release Date: [2024-05-02]

### 🏗️ Breaking changes

- Allow custom timeout for external services - [#485](https://github.com/bakdata/kpops/pull/485)


### 🌀 Miscellaneous

- Update examples for v4 - [#486](https://github.com/bakdata/kpops/pull/486)






## [4.2.1](https://github.com/bakdata/kpops/releases/tag/4.2.1) - Release Date: [2024-04-25]

### 🚀 Features

- Add support for cleaning StatefulSets with PVCs - [#482](https://github.com/bakdata/kpops/pull/482)






## [4.2.0](https://github.com/bakdata/kpops/releases/tag/4.2.0) - Release Date: [2024-04-25]

### 🏭 Refactor

- Improve type annotations for parallel pipeline jobs - [#476](https://github.com/bakdata/kpops/pull/476)


### 🌀 Miscellaneous

- Update Ruff - [#475](https://github.com/bakdata/kpops/pull/475)

- Set Pyright to warn on unknown types - [#480](https://github.com/bakdata/kpops/pull/480)

- Quiet faker debug logs in tests - [#483](https://github.com/bakdata/kpops/pull/483)

- Add pyright matcher - [#481](https://github.com/bakdata/kpops/pull/481)






## [4.1.2](https://github.com/bakdata/kpops/releases/tag/4.1.2) - Release Date: [2024-03-11]

### 📝 Documentation

- fix(docs): Correct `from.components.<component-name>.type` to input - [#473](https://github.com/bakdata/kpops/pull/473)






## [4.1.1](https://github.com/bakdata/kpops/releases/tag/4.1.1) - Release Date: [2024-03-11]

### 🐛 Fixes

- Fix import errors - [#472](https://github.com/bakdata/kpops/pull/472)


### 🏭 Refactor

- Fix import errors - [#472](https://github.com/bakdata/kpops/pull/472)


### 🌀 Miscellaneous

- Update httpx - [#471](https://github.com/bakdata/kpops/pull/471)






## [4.1.0](https://github.com/bakdata/kpops/releases/tag/4.1.0) - Release Date: [2024-03-07]

### 📝 Documentation

- Document precedence between env vars and config.yaml - [#465](https://github.com/bakdata/kpops/pull/465)


### 🌀 Miscellaneous

- Create init command - [#394](https://github.com/bakdata/kpops/pull/394)






## [4.0.2](https://github.com/bakdata/kpops/releases/tag/4.0.2) - Release Date: [2024-03-04]

### 📝 Documentation

- Reference editor plugin for Neovim in docs - [#464](https://github.com/bakdata/kpops/pull/464)


### 🌀 Miscellaneous

- Add support for Python 3.12 - [#467](https://github.com/bakdata/kpops/pull/467)

- Update Pyright - [#468](https://github.com/bakdata/kpops/pull/468)

- Remove package classifiers that are automatically assigned by Poetry - [#469](https://github.com/bakdata/kpops/pull/469)

- Validate autoscaling mandatory fields when enabled - [#470](https://github.com/bakdata/kpops/pull/470)






## [4.0.1](https://github.com/bakdata/kpops/releases/tag/4.0.1) - Release Date: [2024-02-29]

### 🐛 Fixes

- Set supported Python cutoff to 3.11 - [#466](https://github.com/bakdata/kpops/pull/466)






## [4.0.0](https://github.com/bakdata/kpops/releases/tag/4.0.0) - Release Date: [2024-02-27]

### 🏗️ Breaking changes

- Distribute defaults across multiple files - [#438](https://github.com/bakdata/kpops/pull/438)


### 🚀 Features

- Distribute defaults across multiple files - [#438](https://github.com/bakdata/kpops/pull/438)






## [3.2.4](https://github.com/bakdata/kpops/releases/tag/3.2.4) - Release Date: [2024-02-26]

### 🐛 Fixes

- Fix docs CI to include the latest changes to a tagged version in the changelog - [#459](https://github.com/bakdata/kpops/pull/459)

- Fix tempfile creation - [#461](https://github.com/bakdata/kpops/pull/461)

- Fix symbolic link to CONTRIBUTING.md and parallel option in action.yaml - [#462](https://github.com/bakdata/kpops/pull/462)


### 🏭 Refactor

- Refactor Kafka topics - [#447](https://github.com/bakdata/kpops/pull/447)

- Refactor PipelineGenerator to use component ids - [#460](https://github.com/bakdata/kpops/pull/460)


### 📝 Documentation

- Fix docs CI to include the latest changes to a tagged version in the changelog - [#459](https://github.com/bakdata/kpops/pull/459)






## [3.2.3](https://github.com/bakdata/kpops/releases/tag/3.2.3) - Release Date: [2024-02-19]

### 🐛 Fixes

- Trim and hash Helm name override to 63 characters - [#456](https://github.com/bakdata/kpops/pull/456)






## [3.2.2](https://github.com/bakdata/kpops/releases/tag/3.2.2) - Release Date: [2024-02-12]

### 🐛 Fixes

- Fix nested substitution - [#451](https://github.com/bakdata/kpops/pull/451)






## [3.2.1](https://github.com/bakdata/kpops/releases/tag/3.2.1) - Release Date: [2024-02-08]

### 🐛 Fixes

- Fix order of pipeline steps for clean/reset - [#450](https://github.com/bakdata/kpops/pull/450)

- Fix substitution - [#449](https://github.com/bakdata/kpops/pull/449)

- Fix cleaner inheritance, parent model should be aliased during instantiation - [#452](https://github.com/bakdata/kpops/pull/452)


### 🏭 Refactor

- Simplify execution graph logic - [#446](https://github.com/bakdata/kpops/pull/446)






## [3.2.0](https://github.com/bakdata/kpops/releases/tag/3.2.0) - Release Date: [2024-02-01]

### 🚀 Features

- Refactor pipeline filter and add to public API - [#405](https://github.com/bakdata/kpops/pull/405)


### 🏭 Refactor

- Refactor enrichment using Pydantic model validator - [#444](https://github.com/bakdata/kpops/pull/444)

- Refactor pipeline filter and add to public API - [#405](https://github.com/bakdata/kpops/pull/405)


### 📝 Documentation

- Improve Sphinx docs highlighting using RST markup - [#443](https://github.com/bakdata/kpops/pull/443)






## [3.1.0](https://github.com/bakdata/kpops/releases/tag/3.1.0) - Release Date: [2024-01-30]

### 🚀 Features

- Add support for pipeline steps parallelization  - [#312](https://github.com/bakdata/kpops/pull/312)


### 🐛 Fixes

- Update poetry publish workflow version to latest - [#430](https://github.com/bakdata/kpops/pull/430)


### 🏭 Refactor

- Simplify loading of defaults - [#435](https://github.com/bakdata/kpops/pull/435)


### 🌀 Miscellaneous

- Add custom PascalCase to snake_case alias generator - [#436](https://github.com/bakdata/kpops/pull/436)

- Add parallel flag support to kpops runner - [#439](https://github.com/bakdata/kpops/pull/439)






## [3.0.2](https://github.com/bakdata/kpops/releases/tag/3.0.2) - Release Date: [2024-01-23]

### 🐛 Fixes

- Fix Helm diff output - [#434](https://github.com/bakdata/kpops/pull/434)


### 📝 Documentation

- Add step for submodule initialization on the docs - [#431](https://github.com/bakdata/kpops/pull/431)


### 🌀 Miscellaneous

- Add message if examples git submodule is not initialized - [#432](https://github.com/bakdata/kpops/pull/432)

- Update type annotation for deserialized pipeline - [#433](https://github.com/bakdata/kpops/pull/433)






## [3.0.1](https://github.com/bakdata/kpops/releases/tag/3.0.1) - Release Date: [2024-01-19]

### 🐛 Fixes

- Fix broken doc link - [#427](https://github.com/bakdata/kpops/pull/427)

- Add warning log if SR handler is disabled but URL is set - [#428](https://github.com/bakdata/kpops/pull/428)


### 📝 Documentation

- Update docs of word-count example for v3 & new folder structure - [#423](https://github.com/bakdata/kpops/pull/423)

- Move ATM fraud to examples repo - [#425](https://github.com/bakdata/kpops/pull/425)

- Fix broken doc link - [#427](https://github.com/bakdata/kpops/pull/427)


### 🌀 Miscellaneous

- Update pydantic dependency - [#422](https://github.com/bakdata/kpops/pull/422)

- Add git submodule instructions to the contributing.md - [#429](https://github.com/bakdata/kpops/pull/429)






## [3.0.0](https://github.com/bakdata/kpops/releases/tag/3.0.0) - Release Date: [2024-01-17]

### 🏗️ Breaking changes

- Move GitHub action to repository root - [#356](https://github.com/bakdata/kpops/pull/356)

- Make Kafka REST Proxy & Kafka Connect hosts default and improve Schema Registry config - [#354](https://github.com/bakdata/kpops/pull/354)

- Create HelmApp component - [#370](https://github.com/bakdata/kpops/pull/370)

- Change substitution variables separator to `.` - [#388](https://github.com/bakdata/kpops/pull/388)

- Refactor pipeline generator & representation - [#392](https://github.com/bakdata/kpops/pull/392)

- Define custom components module & pipeline base dir globally - [#387](https://github.com/bakdata/kpops/pull/387)

- Use hash and trim long Helm release names instead of only trimming - [#390](https://github.com/bakdata/kpops/pull/390)

- Refactor generate template for Python API usage - [#380](https://github.com/bakdata/kpops/pull/380)

- Namespace substitution vars - [#408](https://github.com/bakdata/kpops/pull/408)

- Refactor streams-bootstrap cleanup jobs as individual HelmApp - [#398](https://github.com/bakdata/kpops/pull/398)

- Refactor Kafka Connector resetter as individual HelmApp - [#400](https://github.com/bakdata/kpops/pull/400)

- Fix wrong Helm release name character limit - [#418](https://github.com/bakdata/kpops/pull/418)


### 🚀 Features

- Allow overriding config files - [#391](https://github.com/bakdata/kpops/pull/391)

- Generate defaults schema - [#402](https://github.com/bakdata/kpops/pull/402)


### 🐛 Fixes

- Fix missing component type in pipeline schema - [#401](https://github.com/bakdata/kpops/pull/401)

- Fix enrichment of nested Pydantic BaseModel - [#415](https://github.com/bakdata/kpops/pull/415)

- Fix wrong Helm release name character limit - [#418](https://github.com/bakdata/kpops/pull/418)

- Update release workflow template to support custom changelog file path - [#421](https://github.com/bakdata/kpops/pull/421)


### 🧪 Dependencies

- Migrate to Pydantic v2 - [#347](https://github.com/bakdata/kpops/pull/347)


### 🏭 Refactor

- Make Kafka REST Proxy & Kafka Connect hosts default and improve Schema Registry config - [#354](https://github.com/bakdata/kpops/pull/354)

- Migrate to Pydantic v2 - [#347](https://github.com/bakdata/kpops/pull/347)

- Refactor pipeline generator & representation - [#392](https://github.com/bakdata/kpops/pull/392)

- Use hash and trim long Helm release names instead of only trimming - [#390](https://github.com/bakdata/kpops/pull/390)

- Refactor Helm `nameOverride` - [#397](https://github.com/bakdata/kpops/pull/397)

- Mark component type as computed Pydantic field - [#399](https://github.com/bakdata/kpops/pull/399)

- Refactor generate template for Python API usage - [#380](https://github.com/bakdata/kpops/pull/380)

- Support multiple inheritance for doc generation - [#406](https://github.com/bakdata/kpops/pull/406)

- Refactor streams-bootstrap cleanup jobs as individual HelmApp - [#398](https://github.com/bakdata/kpops/pull/398)

- Refactor Kafka Connector resetter as individual HelmApp - [#400](https://github.com/bakdata/kpops/pull/400)


### 📝 Documentation

- Move GitHub action to repository root - [#356](https://github.com/bakdata/kpops/pull/356)

- Create HelmApp component - [#370](https://github.com/bakdata/kpops/pull/370)

-  Update docs for substitution variable usage in v3 - [#409](https://github.com/bakdata/kpops/pull/409)

- Support multiple inheritance for doc generation - [#406](https://github.com/bakdata/kpops/pull/406)

- Update docs for v3 - [#416](https://github.com/bakdata/kpops/pull/416)

- Update tests resources - [#417](https://github.com/bakdata/kpops/pull/417)

- Summarize all breaking changes in diffs at the top of the migration guide - [#419](https://github.com/bakdata/kpops/pull/419)


### 🌀 Miscellaneous

- Replace black with ruff - [#365](https://github.com/bakdata/kpops/pull/365)

- Add toml formatter to dprint - [#386](https://github.com/bakdata/kpops/pull/386)

- Add malva to dprint - [#385](https://github.com/bakdata/kpops/pull/385)

- Update KPOps runner with the new options - [#395](https://github.com/bakdata/kpops/pull/395)

- Fix KPOps action to get package from testPyPI - [#396](https://github.com/bakdata/kpops/pull/396)

- KPOps 3.0 - [#420](https://github.com/bakdata/kpops/pull/420)






## [2.0.11](https://github.com/bakdata/kpops/releases/tag/2.0.11) - Release Date: [2023-10-24]

### 🐛 Fixes

- Fix early exit upon Helm exit code 1 - [#376](https://github.com/bakdata/kpops/pull/376)

- Fix docs setup page list indentation - [#377](https://github.com/bakdata/kpops/pull/377)


### 📝 Documentation

- Migrate deprecated mkdocs-material-extensions - [#378](https://github.com/bakdata/kpops/pull/378)

- Fix docs setup page list indentation - [#377](https://github.com/bakdata/kpops/pull/377)

- Exclude resources from docs search - [#371](https://github.com/bakdata/kpops/pull/371)






## [2.0.10](https://github.com/bakdata/kpops/releases/tag/2.0.10) - Release Date: [2023-10-12]

### 🌀 Miscellaneous

- Fix environment variables documentation generation - [#362](https://github.com/bakdata/kpops/pull/362)

- Introduce ruff - [#363](https://github.com/bakdata/kpops/pull/363)

- Print details on connector name mismatch error - [#369](https://github.com/bakdata/kpops/pull/369)

- Enable transparent OS environment lookups from internal environment - [#368](https://github.com/bakdata/kpops/pull/368)






## [2.0.9](https://github.com/bakdata/kpops/releases/tag/2.0.9) - Release Date: [2023-09-19]

### 🐛 Fixes

- Fix Kafka connect config name for deletion - [#361](https://github.com/bakdata/kpops/pull/361)


### 📝 Documentation

- Fix link to kpops-examples - [#357](https://github.com/bakdata/kpops/pull/357)






## [2.0.8](https://github.com/bakdata/kpops/releases/tag/2.0.8) - Release Date: [2023-09-06]

### 🐛 Fixes

- Fix config.yaml overriding environment variables - [#353](https://github.com/bakdata/kpops/pull/353)


### 🏭 Refactor

- Refactor component prefix & name - [#326](https://github.com/bakdata/kpops/pull/326)

- Remove unnecessary condition during inflate - [#328](https://github.com/bakdata/kpops/pull/328)






## [2.0.7](https://github.com/bakdata/kpops/releases/tag/2.0.7) - Release Date: [2023-08-31]

### 🐛 Fixes

- Print only rendered templates when `--template` flag is set - [#350](https://github.com/bakdata/kpops/pull/350)


### 📝 Documentation

- Add migration guide - [#352](https://github.com/bakdata/kpops/pull/352)






## [2.0.6](https://github.com/bakdata/kpops/releases/tag/2.0.6) - Release Date: [2023-08-30]

### 🏭 Refactor

- Simplify deployment with local Helm charts - [#349](https://github.com/bakdata/kpops/pull/349)






## [2.0.5](https://github.com/bakdata/kpops/releases/tag/2.0.5) - Release Date: [2023-08-30]

### 🐛 Fixes

- Fix versioning of docs when releasing - [#346](https://github.com/bakdata/kpops/pull/346)






## [2.0.4](https://github.com/bakdata/kpops/releases/tag/2.0.4) - Release Date: [2023-08-29]

### 🐛 Fixes

- Fix GitHub ref variable for pushing docs to main branch - [#343](https://github.com/bakdata/kpops/pull/343)


### 📝 Documentation

- Add `dprint` as the markdown formatter - [#337](https://github.com/bakdata/kpops/pull/337)

- Publish pre-release docs for PRs & main branch - [#339](https://github.com/bakdata/kpops/pull/339)

- Align docs colours - [#345](https://github.com/bakdata/kpops/pull/345)


### 🌀 Miscellaneous

- Exclude abstract components from pipeline schema - [#332](https://github.com/bakdata/kpops/pull/332)






## [2.0.3](https://github.com/bakdata/kpops/releases/tag/2.0.3) - Release Date: [2023-08-24]

### 🐛 Fixes

- Fix GitHub action error in non-Python projects - [#340](https://github.com/bakdata/kpops/pull/340)


### 🌀 Miscellaneous

- Lint GitHub action - [#342](https://github.com/bakdata/kpops/pull/342)






## [2.0.2](https://github.com/bakdata/kpops/releases/tag/2.0.2) - Release Date: [2023-08-23]

### 📝 Documentation

- Add version dropdown to the documentation - [#336](https://github.com/bakdata/kpops/pull/336)

- Break the documentation down into smaller subsection - [#329](https://github.com/bakdata/kpops/pull/329)






## [2.0.1](https://github.com/bakdata/kpops/releases/tag/2.0.1) - Release Date: [2023-08-22]

### 🐛 Fixes

- Fix optional flags in GitHub action - [#334](https://github.com/bakdata/kpops/pull/334)






## [2.0.0](https://github.com/bakdata/kpops/releases/tag/2.0.0) - Release Date: [2023-08-17]

### 🏗️ Breaking changes

- Remove camel case conversion of internal models - [#308](https://github.com/bakdata/kpops/pull/308)

- Derive component type automatically from class name - [#309](https://github.com/bakdata/kpops/pull/309)

- Refactor input/output types - [#232](https://github.com/bakdata/kpops/pull/232)

- v2 - [#321](https://github.com/bakdata/kpops/pull/321)


### 🚀 Features

- Automatically support schema generation for custom components - [#307](https://github.com/bakdata/kpops/pull/307)

- Derive component type automatically from class name - [#309](https://github.com/bakdata/kpops/pull/309)


### 🏭 Refactor

- Refactor input/output types - [#232](https://github.com/bakdata/kpops/pull/232)


### 📝 Documentation

- Fix editor integration example in docs - [#273](https://github.com/bakdata/kpops/pull/273)






## [1.7.2](https://github.com/bakdata/kpops/releases/tag/1.7.2) - Release Date: [2023-08-16]

### 🏭 Refactor

- Refactor Kafka Connect handler - [#322](https://github.com/bakdata/kpops/pull/322)


### 📝 Documentation

- Add KPOps Runner GitHub Action to the documentation - [#325](https://github.com/bakdata/kpops/pull/325)

- Remove `:type` and `:rtype` from docstrings - [#324](https://github.com/bakdata/kpops/pull/324)






## [1.7.1](https://github.com/bakdata/kpops/releases/tag/1.7.1) - Release Date: [2023-08-15]

### 📝 Documentation

- Modularize and autogenerate examples for the documentation - [#267](https://github.com/bakdata/kpops/pull/267)

- Update the variable documentation - [#266](https://github.com/bakdata/kpops/pull/266)






## [1.7.0](https://github.com/bakdata/kpops/releases/tag/1.7.0) - Release Date: [2023-08-15]

### 🚀 Features

- Add flag to exclude pipeline steps - [#300](https://github.com/bakdata/kpops/pull/300)






## [1.6.0](https://github.com/bakdata/kpops/releases/tag/1.6.0) - Release Date: [2023-08-10]

### 🏭 Refactor

- Refactor handling of Helm flags - [#319](https://github.com/bakdata/kpops/pull/319)






## [1.5.0](https://github.com/bakdata/kpops/releases/tag/1.5.0) - Release Date: [2023-08-10]

### 🚀 Features

- Refactor Helm wrapper and add `--set-file` flag - [#311](https://github.com/bakdata/kpops/pull/311)


### 🏭 Refactor

- Refactor Helm wrapper and add `--set-file` flag - [#311](https://github.com/bakdata/kpops/pull/311)

- Set default for ToSection topics - [#313](https://github.com/bakdata/kpops/pull/313)

- Annotate types for ToSection models mapping - [#315](https://github.com/bakdata/kpops/pull/315)


### 🌀 Miscellaneous

- Check Poetry lock file consistency - [#316](https://github.com/bakdata/kpops/pull/316)






## [1.4.0](https://github.com/bakdata/kpops/releases/tag/1.4.0) - Release Date: [2023-08-02]

### 🐛 Fixes

- Validate unique step names - [#292](https://github.com/bakdata/kpops/pull/292)


### 🏭 Refactor

- Order PipelineComponent fields - [#290](https://github.com/bakdata/kpops/pull/290)

- Migrate requests to httpx - [#302](https://github.com/bakdata/kpops/pull/302)

- Refactor CLI using dtyper - [#306](https://github.com/bakdata/kpops/pull/306)


### 🌀 Miscellaneous

- Update Black - [#294](https://github.com/bakdata/kpops/pull/294)

- Fix vulnerability in mkdocs-material - [#295](https://github.com/bakdata/kpops/pull/295)

- Move breaking changes section upper in the change log config - [#287](https://github.com/bakdata/kpops/pull/287)






## [1.3.2](https://github.com/bakdata/kpops/releases/tag/1.3.2) - Release Date: [2023-07-13]

### 🐛 Fixes

- Exclude Helm tests from dry-run diff - [#293](https://github.com/bakdata/kpops/pull/293)






## [1.3.1](https://github.com/bakdata/kpops/releases/tag/1.3.1) - Release Date: [2023-07-11]

### 🏭 Refactor

- Remove workaround for pipeline steps - [#276](https://github.com/bakdata/kpops/pull/276)


### 🌀 Miscellaneous

- Update codeowners - [#281](https://github.com/bakdata/kpops/pull/281)

- Reactivate Windows CI - [#255](https://github.com/bakdata/kpops/pull/255)

- Downgrade Poetry version on the Windows CI pipeline - [#286](https://github.com/bakdata/kpops/pull/286)

- Set ANSI theme for output of `kpops generate` - [#289](https://github.com/bakdata/kpops/pull/289)






## [1.3.0](https://github.com/bakdata/kpops/releases/tag/1.3.0) - Release Date: [2023-07-07]

### 🏭 Refactor

- Plural broker field in pipeline config - [#278](https://github.com/bakdata/kpops/pull/278)


### 📝 Documentation

- Update KPOps runner readme for dev versions - [#279](https://github.com/bakdata/kpops/pull/279)


### 🏗️ Breaking changes

- Plural broker field in pipeline config - [#278](https://github.com/bakdata/kpops/pull/278)


### 🌀 Miscellaneous

- Add breaking changes section to change log config - [#280](https://github.com/bakdata/kpops/pull/280)






## [1.2.4](https://github.com/bakdata/kpops/releases/tag/1.2.4) - Release Date: [2023-06-27]

### 🌀 Miscellaneous

- Update changelog action to contain miscellaneous PRs - [#269](https://github.com/bakdata/kpops/pull/269)






## [1.2.3](https://github.com/bakdata/kpops/releases/tag/1.2.3) - Release Date: [2023-06-22]

### 🐛 Fixes

- Refactor custom component validation & hide field from kpops output - [#265](https://github.com/bakdata/kpops/pull/265)


### 🏭 Refactor

- Refactor custom component validation & hide field from kpops output - [#265](https://github.com/bakdata/kpops/pull/265)




### 🌀 Miscellaneous



## [1.2.2](https://github.com/bakdata/kpops/releases/tag/1.2.2) - Release Date: [2023-06-21]



### 🌀 Miscellaneous

- Create workflow to lint CI - [#260](https://github.com/bakdata/kpops/pull/260)

- Fix update docs when releasing - [#261](https://github.com/bakdata/kpops/pull/261)

- Rename change log message for uncategorized issues - [#262](https://github.com/bakdata/kpops/pull/262)



## [1.2.1](https://github.com/bakdata/kpops/releases/tag/1.2.1) - Release Date: [2023-06-21]



<summary>Uncategorized</summary>

- Fix update docs in release workflow - [#258](https://github.com/bakdata/kpops/pull/258)



## [1.2.0](https://github.com/bakdata/kpops/releases/tag/1.2.0) - Release Date: [2023-06-21]

### 🚀 Features

- Add `helm repo update <repo-name>` for Helm >3.7 - [#239](https://github.com/bakdata/kpops/pull/239)


### 🐛 Fixes

- add --namespace option to Helm template command - [#237](https://github.com/bakdata/kpops/pull/237)

- Add missing type annotation for Pydantic attributes - [#238](https://github.com/bakdata/kpops/pull/238)

- Fix helm version check - [#242](https://github.com/bakdata/kpops/pull/242)

- Fix Helm Version Check - [#244](https://github.com/bakdata/kpops/pull/244)

- Fix import from external module - [#256](https://github.com/bakdata/kpops/pull/256)


### 🏭 Refactor

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




