# Changelog

All notable changes to this project will be documented in this file.

## [10.4.1](https://github.com/bakdata/kpops/tree/10.4.1) - 2025-05-07
### What's changed

* ci: upstream Python uv release workflow by @disrupted in [#627](https://github.com/bakdata/kpops/pull/627)

* fix(pipeline-generator): clear env on load YAML by @disrupted in [#628](https://github.com/bakdata/kpops/pull/628)


**Full Changelog**: https://github.com/bakdata/kpops/compare/10.4.0...10.4.1

## [10.4.0](https://github.com/bakdata/kpops/tree/10.4.0) - 2025-04-08
### What's changed

* feat(helm-app): set fullnameOverride by @philipp94831 in [#626](https://github.com/bakdata/kpops/pull/626)

* Bump version 10.3.0 → 10.4.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/10.3.0...10.4.0

## [10.3.0](https://github.com/bakdata/kpops/tree/10.3.0) - 2025-04-07
### What's changed

* feat(helm-app): add properties to generate output by @philipp94831 in [#624](https://github.com/bakdata/kpops/pull/624)

* refactor(pipeline): set custom attribute order by @disrupted in [#625](https://github.com/bakdata/kpops/pull/625)

* Bump version 10.2.0 → 10.3.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/10.2.0...10.3.0

## [10.2.0](https://github.com/bakdata/kpops/tree/10.2.0) - 2025-04-02
### What's changed

* feat: add substitution variable `${pipeline.parent.name}` by @jkbe in [#582](https://github.com/bakdata/kpops/pull/582)

* Bump version 10.1.3 → 10.2.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/10.1.3...10.2.0

## [10.1.3](https://github.com/bakdata/kpops/tree/10.1.3) - 2025-04-01
### What's changed

* refactor(helm): cache repos and version across components by @daconstenla in [#622](https://github.com/bakdata/kpops/pull/622)

* Bump version 10.1.2 → 10.1.3 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/10.1.2...10.1.3

## [10.1.2](https://github.com/bakdata/kpops/tree/10.1.2) - 2025-03-26
### What's changed

* feat(pipeline): add `generate` method by @disrupted in [#620](https://github.com/bakdata/kpops/pull/620)

* test(kafka-connect-api): improve & speed up tests by @disrupted in [#618](https://github.com/bakdata/kpops/pull/618)

* fix(pipeline): fix Pydantic TypeError by @disrupted in [#623](https://github.com/bakdata/kpops/pull/623)

* Bump version 10.1.1 → 10.1.2 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/10.1.1...10.1.2

## [10.1.1](https://github.com/bakdata/kpops/tree/10.1.1) - 2025-03-25
### What's changed

* fix(kafka-connector): parse enum correctly by @disrupted in [#619](https://github.com/bakdata/kpops/pull/619)

* Bump version 10.1.0 → 10.1.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/10.1.0...10.1.1

## [10.1.0](https://github.com/bakdata/kpops/tree/10.1.0) - 2025-03-20
### What's changed

* feat(kafka-connect): set connector state by @disrupted in [#616](https://github.com/bakdata/kpops/pull/616)

* Bump version 10.0.4 → 10.1.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/10.0.4...10.1.0

## [10.0.4](https://github.com/bakdata/kpops/tree/10.0.4) - 2025-03-13
### What's changed

* Support streams-bootstrap v4 by @philipp94831 in [#617](https://github.com/bakdata/kpops/pull/617)

* Bump version 10.0.3 → 10.0.4 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/10.0.3...10.0.4

## [10.0.3](https://github.com/bakdata/kpops/tree/10.0.3) - 2025-03-06
### What's changed

* refactor(api): improve typing by @disrupted in [#612](https://github.com/bakdata/kpops/pull/612)

* refactor(pydantic): create `SkipGenerate` type by @disrupted in [#611](https://github.com/bakdata/kpops/pull/611)

* refactor(cli): use annotated for typer option by @disrupted in [#613](https://github.com/bakdata/kpops/pull/613)

* fix(kafka-connector): destroy connector on reset by @disrupted in [#615](https://github.com/bakdata/kpops/pull/615)

* Bump version 10.0.2 → 10.0.3 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/10.0.2...10.0.3

## [10.0.2](https://github.com/bakdata/kpops/tree/10.0.2) - 2025-03-04
### What's changed

* fix: hide _cleaner & _resetter from generate output by @disrupted in [#610](https://github.com/bakdata/kpops/pull/610)

* Bump version 10.0.1 → 10.0.2 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/10.0.1...10.0.2

## [10.0.1](https://github.com/bakdata/kpops/tree/10.0.1) - 2025-03-04
### What's changed

* chore: upgrade ruff by @disrupted in [#606](https://github.com/bakdata/kpops/pull/606)

* refactor(helm-app): make handlers private by @disrupted in [#602](https://github.com/bakdata/kpops/pull/602)

* refactor: switch to basedpyright by @disrupted in [#604](https://github.com/bakdata/kpops/pull/604)

* fix(helm-app): hide repo_config & diff_config from generate output by @disrupted in [#607](https://github.com/bakdata/kpops/pull/607)

* fix(cleaner): enrich on init by @disrupted in [#608](https://github.com/bakdata/kpops/pull/608)

* Bump version 10.0.0 → 10.0.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/10.0.0...10.0.1

## [10.0.0](https://github.com/bakdata/kpops/tree/10.0.0) - 2025-02-27
### What's changed

* refactor(helm-diff)!: define ignore keypath as array by @disrupted in [#600](https://github.com/bakdata/kpops/pull/600)

* refactor(helm-diff)!: configure on HelmApp component level by @disrupted in [#601](https://github.com/bakdata/kpops/pull/601)

* docs: create migration guide for v10 by @disrupted in [#603](https://github.com/bakdata/kpops/pull/603)

* Bump version 9.4.1 → 10.0.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/9.4.1...10.0.0

## [9.4.1](https://github.com/bakdata/kpops/tree/9.4.1) - 2025-02-26
### What's changed

* refactor(streams-bootstrap): update JMX remote specification by @philipp94831 in [#599](https://github.com/bakdata/kpops/pull/599)

* Bump version 9.4.0 → 9.4.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/9.4.0...9.4.1

## [9.4.0](https://github.com/bakdata/kpops/tree/9.4.0) - 2025-02-24
### What's changed

* refactor(streams-bootstrap): update JMX specification by @philipp94831 in [#597](https://github.com/bakdata/kpops/pull/597)

* Bump version 9.3.0 → 9.4.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/9.3.0...9.4.0

## [9.3.0](https://github.com/bakdata/kpops/tree/9.3.0) - 2025-02-03
### What's changed

* Use Pydantic `model_validate` to avoid Pyright warnings by @disrupted in [#586](https://github.com/bakdata/kpops/pull/586)

* Fix release commit message by @disrupted in [#591](https://github.com/bakdata/kpops/pull/591)

* Configure PyPI trusted publishing by @yannick-roeder in [#592](https://github.com/bakdata/kpops/pull/592)

* Migrate pre-commit hooks to lefthook by @disrupted in [#584](https://github.com/bakdata/kpops/pull/584)

* feat: support symbolic linked pipelines to avoid repetition by @daconstenla in [#580](https://github.com/bakdata/kpops/pull/580)

* fix: address CI warnings introduced by #580 by @disrupted in [#594](https://github.com/bakdata/kpops/pull/594)

* feat(streams-bootstrap): allow float values in command line by @disrupted in [#593](https://github.com/bakdata/kpops/pull/593)

* ci: run lint job only for target Python version on Linux by @disrupted in [#596](https://github.com/bakdata/kpops/pull/596)

* style: format YAML & JSON by @disrupted in [#595](https://github.com/bakdata/kpops/pull/595)

* feat: support custom namespace configuration for `StrimziKafkaTopic` by @daconstenla in [#581](https://github.com/bakdata/kpops/pull/581)

* Bump version 9.2.1 → 9.3.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/9.2.1...9.3.0

## [9.2.1](https://github.com/bakdata/kpops/tree/9.2.1) - 2025-01-15
### What's changed

* Fix CI release and changelog by @disrupted in [#590](https://github.com/bakdata/kpops/pull/590)

* Bump version 9.2.1-dev → 9.2.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/9.2.0-dev...9.2.1

## [9.2.0-dev](https://github.com/bakdata/kpops/tree/9.2.0-dev) - 2025-01-14
### What's changed

* Improve Pyright matcher by @disrupted in [#579](https://github.com/bakdata/kpops/pull/579)

* Migrate from Poetry to uv by @disrupted in [#578](https://github.com/bakdata/kpops/pull/578)

* Fix circular imports when running individual tests by @disrupted in [#583](https://github.com/bakdata/kpops/pull/583)

* Configure Pyright to report import cycles by @disrupted in [#585](https://github.com/bakdata/kpops/pull/585)

* Fix kpops package build by @disrupted in [#588](https://github.com/bakdata/kpops/pull/588)

* Fail if streams-boostrap v3 model is instantiated with v2 attribute by @disrupted in [#587](https://github.com/bakdata/kpops/pull/587)

* Bump version 9.1.0 → 9.2.0-dev by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/9.1.0...9.2.0-dev

## [9.1.0](https://github.com/bakdata/kpops/tree/9.1.0) - 2025-01-07
### What's changed

* Update CODEOWNERS in [#572](https://github.com/bakdata/kpops/pull/572)

* Update test components to streams-bootstrap v3 by @disrupted in [#576](https://github.com/bakdata/kpops/pull/576)

* Silence deprecation warnings for streams-bootstrap v2 in tests by @disrupted in [#577](https://github.com/bakdata/kpops/pull/577)

* Represent multiline strings using YAML block style by @disrupted in [#574](https://github.com/bakdata/kpops/pull/574)

* Indent sequence items to follow style recommendations by @disrupted in [#575](https://github.com/bakdata/kpops/pull/575)

* Bump version 9.0.1 → 9.1.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/9.0.1...9.1.0

## [9.0.1](https://github.com/bakdata/kpops/tree/9.0.1) - 2024-12-20
### What's changed

* Add operation-mode documentation to mkdocs index in [#573](https://github.com/bakdata/kpops/pull/573)

* Bump version 9.0.0 → 9.0.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/9.0.0...9.0.1

## [9.0.0](https://github.com/bakdata/kpops/tree/9.0.0) - 2024-12-20
### What's changed

* Merge main

* Add topic manifestation of ProducerApps for reset command in [#566](https://github.com/bakdata/kpops/pull/566)

* Add documentation for operation-mode in KPOps in [#565](https://github.com/bakdata/kpops/pull/565)

* Merge branch 'main' into v9

* Merge branch 'v9' of github.com:bakdata/kpops into v9

* Set Python target version to 3.11 by @disrupted

* Hide `operation_mode` from KPOps config in [#571](https://github.com/bakdata/kpops/pull/571)

* Add migration guide v8-v9 in [#562](https://github.com/bakdata/kpops/pull/562)

* KPOps V9 in [#558](https://github.com/bakdata/kpops/pull/558)

* Bump version 8.4.0 → 9.0.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/8.4.0...9.0.0

## [8.4.0](https://github.com/bakdata/kpops/tree/8.4.0) - 2024-12-18
### What's changed

* Create generic `SerializeAsOptional` type for Pydantic by @disrupted in [#564](https://github.com/bakdata/kpops/pull/564)

* Bump version 8.3.2 → 8.4.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/8.3.2...8.4.0

## [8.3.2](https://github.com/bakdata/kpops/tree/8.3.2) - 2024-12-17
### What's changed

* Fix allow optional resources requests and limits by @disrupted in [#570](https://github.com/bakdata/kpops/pull/570)

* Bump version 8.3.1 → 8.3.2 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/8.3.1...8.3.2

## [8.3.1](https://github.com/bakdata/kpops/tree/8.3.1) - 2024-12-17
### What's changed

* Fix Kubernetes memory not accepting decimal values by @disrupted in [#568](https://github.com/bakdata/kpops/pull/568)

* Add ephemeral storage to Kubernetes resource requests and limits by @disrupted in [#569](https://github.com/bakdata/kpops/pull/569)

* Bump version 8.3.0 → 8.3.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/8.3.0...8.3.1

## [8.3.0](https://github.com/bakdata/kpops/tree/8.3.0) - 2024-12-17
### What's changed

* Merge branch 'main' into v9

* Drop support for Python 3.10 by @disrupted in [#561](https://github.com/bakdata/kpops/pull/561)

* Manifest Kubernetes resources for `reset` command in [#563](https://github.com/bakdata/kpops/pull/563)

* Add Kubernetes affinity and tolerations to streams-bootstrap v2 values by @disrupted in [#567](https://github.com/bakdata/kpops/pull/567)

* Bump version 8.2.0 → 8.3.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/8.2.0...8.3.0

## [8.2.0](https://github.com/bakdata/kpops/tree/8.2.0) - 2024-12-12
### What's changed

* merge

* Manifest toSection with Strimzi KafkaTopic in [#545](https://github.com/bakdata/kpops/pull/545)

* Manifest Kubernetes resources for `destroy` command in [#552](https://github.com/bakdata/kpops/pull/552)

* Bump streams-bootstrap to 3.1.0 by @disrupted in [#557](https://github.com/bakdata/kpops/pull/557)

* Merge branch 'main' into v9

* Manifest Kubernetes resources for `clean` command in [#559](https://github.com/bakdata/kpops/pull/559)

* Update KPOps example snapshots and fix broken link to defaults.yaml in [#560](https://github.com/bakdata/kpops/pull/560)

* Merge branch 'main' into v9

* Add Pydantic models for Kubernetes Affinity by @disrupted in [#555](https://github.com/bakdata/kpops/pull/555)

* Bump version 8.1.4 → 8.2.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/8.1.4...8.2.0

## [8.1.4](https://github.com/bakdata/kpops/tree/8.1.4) - 2024-12-09
### What's changed

* Fix `kpops --version` by @disrupted in [#551](https://github.com/bakdata/kpops/pull/551)

* Trim Helm name override for Producer CronJob to 52 characters by @disrupted in [#550](https://github.com/bakdata/kpops/pull/550)

* Bump version 8.1.3 → 8.1.4 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/8.1.3...8.1.4

## [8.1.3](https://github.com/bakdata/kpops/tree/8.1.3) - 2024-12-05
### What's changed

* Merge branch 'main' of github.com:bakdata/kpops into v9

* Remove repeated defaults from streams-bootstrap values by @disrupted in [#547](https://github.com/bakdata/kpops/pull/547)

* Bump version 8.1.2 → 8.1.3 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/8.1.2...8.1.3

## [8.1.2](https://github.com/bakdata/kpops/tree/8.1.2) - 2024-12-04
### What's changed

* Introduce KPOps operation and manifest resources for deployment in [#541](https://github.com/bakdata/kpops/pull/541)

* Define Pydantic model to representing Kubernetes manifest in [#546](https://github.com/bakdata/kpops/pull/546)

* Convert all values of Kafka connector and topic config to string by @disrupted in [#544](https://github.com/bakdata/kpops/pull/544)

* Bump version 8.1.1 → 8.1.2 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/8.1.1...8.1.2

## [8.1.1](https://github.com/bakdata/kpops/tree/8.1.1) - 2024-12-02
### What's changed

* Fix `files` field value type in Streamsboostrap component in [#542](https://github.com/bakdata/kpops/pull/542)

* Fix: Use enum values when dumping models in [#543](https://github.com/bakdata/kpops/pull/543)

* Bump version 8.1.0 → 8.1.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/8.1.0...8.1.1

## [8.1.0](https://github.com/bakdata/kpops/tree/8.1.0) - 2024-10-25
### What's changed

* Upgrade typer to support union types in [#533](https://github.com/bakdata/kpops/pull/533)

* Extend StreamsBootstrap model in [#534](https://github.com/bakdata/kpops/pull/534)

* Bump version 8.0.1 → 8.1.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/8.0.1...8.1.0

## [8.0.1](https://github.com/bakdata/kpops/tree/8.0.1) - 2024-08-22
### What's changed

* Fix changelog in docs in [#532](https://github.com/bakdata/kpops/pull/532)

* Bump version 8.0.0 → 8.0.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/8.0.0...8.0.1

## [8.0.0](https://github.com/bakdata/kpops/tree/8.0.0) - 2024-08-21
### What's changed

* Make KafkaApp responsible of deploying/cleaning streams bootstrap components (#522)

* Add support for streams-bootstrap v3 (#519)

* Rename role to label (#525)

* Fix Pyright warning about type override without default value (#524) by @disrupted

* Remove v3 and suffix old streams bootstrap with v2 (#526)

* KPOps `8.0.0` in [#531](https://github.com/bakdata/kpops/pull/531)

* Bump version 7.1.0 → 8.0.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/7.1.0...8.0.0

## [7.1.0](https://github.com/bakdata/kpops/tree/7.1.0) - 2024-08-15
### What's changed

* Improve incomplete type hints by @disrupted in [#515](https://github.com/bakdata/kpops/pull/515)

* Fallback to user defined model when the validation of cluster model fails in [#521](https://github.com/bakdata/kpops/pull/521)

* Fix incorrect parameter type annotation by @disrupted in [#523](https://github.com/bakdata/kpops/pull/523)

* Update pytest by @disrupted in [#527](https://github.com/bakdata/kpops/pull/527)

* Replace kubernetes-asyncio with lightkube by @disrupted in [#517](https://github.com/bakdata/kpops/pull/517)

* Bump version 7.0.0 → 7.1.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/7.0.0...7.1.0

## [7.0.0](https://github.com/bakdata/kpops/tree/7.0.0) - 2024-07-23
### What's changed

* Merge remote-tracking branch 'origin/main' into v7 by @disrupted

* Call destroy from inside of reset or clean in [#501](https://github.com/bakdata/kpops/pull/501)

* clean/reset streams-bootstrap components with cluster values in [#498](https://github.com/bakdata/kpops/pull/498)

* Rename app field by @disrupted in [#506](https://github.com/bakdata/kpops/pull/506)

* Fix circular dependency when running individual tests

* Add tests for global config & handlers by @disrupted

* Update examples by @disrupted

* Bump version 6.1.0 → 7.0.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/6.1.0...7.0.0

## [6.1.0](https://github.com/bakdata/kpops/tree/6.1.0) - 2024-07-09
### What's changed

* Add image tag field to streams-bootstrap app values in [#499](https://github.com/bakdata/kpops/pull/499)

* Automatic loading of namespaced custom components by @disrupted in [#500](https://github.com/bakdata/kpops/pull/500)

* Improve dataclass instance check by @disrupted in [#507](https://github.com/bakdata/kpops/pull/507)

* Delete ignored keys from diff by @disrupted in [#510](https://github.com/bakdata/kpops/pull/510)

* Bump version 6.0.2 → 6.1.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/6.0.2...6.1.0

## [6.0.2](https://github.com/bakdata/kpops/tree/6.0.2) - 2024-07-04
### What's changed

* Update codeowners by @disrupted in [#504](https://github.com/bakdata/kpops/pull/504)

* Generate developer docs for Python API by @sujuka99 in [#503](https://github.com/bakdata/kpops/pull/503)

* Bump version 6.0.1 → 6.0.2 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/6.0.1...6.0.2

## [6.0.1](https://github.com/bakdata/kpops/tree/6.0.1) - 2024-06-12
### What's changed

* Fix connector resetter offset topic by @disrupted in [#497](https://github.com/bakdata/kpops/pull/497)

* Bump version 6.0.0 → 6.0.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/6.0.0...6.0.1

## [6.0.0](https://github.com/bakdata/kpops/tree/6.0.0) - 2024-06-06
### What's changed

* KPOps `6.0.0` in [#496](https://github.com/bakdata/kpops/pull/496)

* Bump version 5.1.1 → 6.0.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/5.1.1...6.0.0

## [5.1.1](https://github.com/bakdata/kpops/tree/5.1.1) - 2024-05-22
### What's changed

* Add YAML separator (---) to stdout in [#491](https://github.com/bakdata/kpops/pull/491)

* Bump version 5.1.0 → 5.1.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/5.1.0...5.1.1

## [5.1.0](https://github.com/bakdata/kpops/tree/5.1.0) - 2024-05-22
### What's changed

* Add computed field for Helm release name and name override by @disrupted in [#490](https://github.com/bakdata/kpops/pull/490)

* Bump version 5.0.1 → 5.1.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/5.0.1...5.1.0

## [5.0.1](https://github.com/bakdata/kpops/tree/5.0.1) - 2024-05-15
### What's changed

* Fix missing await on Kubernetes API in [#488](https://github.com/bakdata/kpops/pull/488)

* Bump version 5.0.0 → 5.0.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/5.0.0...5.0.1

## [5.0.0](https://github.com/bakdata/kpops/tree/5.0.0) - 2024-05-02
### What's changed

* Update examples for v4 by @disrupted in [#486](https://github.com/bakdata/kpops/pull/486)

* Allow custom timeout for external services by @disrupted in [#485](https://github.com/bakdata/kpops/pull/485)

* Bump version 4.2.1 → 5.0.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/4.2.1...5.0.0

## [4.2.1](https://github.com/bakdata/kpops/tree/4.2.1) - 2024-04-25
### What's changed

* Add support for cleaning StatefulSets with PVCs in [#482](https://github.com/bakdata/kpops/pull/482)

* Bump version 4.2.0 → 4.2.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/4.2.0...4.2.1

## [4.2.0](https://github.com/bakdata/kpops/tree/4.2.0) - 2024-04-25
### What's changed

* Update Ruff by @disrupted in [#475](https://github.com/bakdata/kpops/pull/475)

* Improve type annotations for parallel pipeline jobs by @disrupted in [#476](https://github.com/bakdata/kpops/pull/476)

* Set Pyright to warn on unknown types by @disrupted in [#480](https://github.com/bakdata/kpops/pull/480)

* Quiet faker debug logs in tests by @disrupted in [#483](https://github.com/bakdata/kpops/pull/483)

* Add pyright matcher by @sujuka99 in [#481](https://github.com/bakdata/kpops/pull/481)

* Bump version 4.1.2 → 4.2.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/4.1.2...4.2.0

## [4.1.2](https://github.com/bakdata/kpops/tree/4.1.2) - 2024-03-11
### What's changed

* fix(docs): Correct `from.components.<component-name>.type` to input in [#473](https://github.com/bakdata/kpops/pull/473)

* Bump version 4.1.1 → 4.1.2 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/4.1.1...4.1.2

## [4.1.1](https://github.com/bakdata/kpops/tree/4.1.1) - 2024-03-11
### What's changed

* Update httpx by @disrupted in [#471](https://github.com/bakdata/kpops/pull/471)

* Fix import errors by @sujuka99 in [#472](https://github.com/bakdata/kpops/pull/472)

* Bump version 4.1.0 → 4.1.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/4.1.0...4.1.1

## [4.1.0](https://github.com/bakdata/kpops/tree/4.1.0) - 2024-03-07
### What's changed

* Document precedence between env vars and config.yaml by @jkbe in [#465](https://github.com/bakdata/kpops/pull/465)

* Create init command by @sujuka99 in [#394](https://github.com/bakdata/kpops/pull/394)

* Bump version 4.0.2 → 4.1.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/4.0.2...4.1.0

## [4.0.2](https://github.com/bakdata/kpops/tree/4.0.2) - 2024-03-04
### What's changed

* Add support for Python 3.12 by @disrupted in [#467](https://github.com/bakdata/kpops/pull/467)

* Update Pyright by @disrupted in [#468](https://github.com/bakdata/kpops/pull/468)

* Remove package classifiers that are automatically assigned by Poetry by @disrupted in [#469](https://github.com/bakdata/kpops/pull/469)

* Reference editor plugin for Neovim in docs by @disrupted in [#464](https://github.com/bakdata/kpops/pull/464)

* Validate autoscaling mandatory fields when enabled in [#470](https://github.com/bakdata/kpops/pull/470)

* Bump version 4.0.1 → 4.0.2 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/4.0.1...4.0.2

## [4.0.1](https://github.com/bakdata/kpops/tree/4.0.1) - 2024-02-29
### What's changed

* Set supported Python cutoff to 3.11 by @disrupted in [#466](https://github.com/bakdata/kpops/pull/466)

* Bump version 4.0.0 → 4.0.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/4.0.0...4.0.1

## [4.0.0](https://github.com/bakdata/kpops/tree/4.0.0) - 2024-02-27
### What's changed

* Distribute defaults across multiple files in [#438](https://github.com/bakdata/kpops/pull/438)

* Bump version 3.2.4 → 4.0.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/3.2.4...4.0.0

## [3.2.4](https://github.com/bakdata/kpops/tree/3.2.4) - 2024-02-26
### What's changed

* Refactor Kafka topics by @disrupted in [#447](https://github.com/bakdata/kpops/pull/447)

* Fix docs CI to include the latest changes to a tagged version in the changelog by @sujuka99 in [#459](https://github.com/bakdata/kpops/pull/459)

* Refactor PipelineGenerator to use component ids by @disrupted in [#460](https://github.com/bakdata/kpops/pull/460)

* Fix tempfile creation by @sujuka99 in [#461](https://github.com/bakdata/kpops/pull/461)

* Fix symbolic link to CONTRIBUTING.md and parallel option in action.yaml in [#462](https://github.com/bakdata/kpops/pull/462)

* Bump version 3.2.3 → 3.2.4 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/3.2.3...3.2.4

## [3.2.3](https://github.com/bakdata/kpops/tree/3.2.3) - 2024-02-19
### What's changed

* Trim and hash Helm name override to 63 characters by @disrupted in [#456](https://github.com/bakdata/kpops/pull/456)

* Bump version 3.2.2 → 3.2.3 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/3.2.2...3.2.3

## [3.2.2](https://github.com/bakdata/kpops/tree/3.2.2) - 2024-02-12
### What's changed

* Fix nested substitution by @sujuka99 in [#451](https://github.com/bakdata/kpops/pull/451)

* Bump version 3.2.1 → 3.2.2 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/3.2.1...3.2.2

## [3.2.1](https://github.com/bakdata/kpops/tree/3.2.1) - 2024-02-08
### What's changed

* Simplify execution graph logic by @disrupted in [#446](https://github.com/bakdata/kpops/pull/446)

* Fix order of pipeline steps for clean/reset by @disrupted in [#450](https://github.com/bakdata/kpops/pull/450)

* Fix substitution by @sujuka99 in [#449](https://github.com/bakdata/kpops/pull/449)

* Fix cleaner inheritance, parent model should be aliased during instantiation by @disrupted in [#452](https://github.com/bakdata/kpops/pull/452)

* Bump version 3.2.0 → 3.2.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/3.2.0...3.2.1

## [3.2.0](https://github.com/bakdata/kpops/tree/3.2.0) - 2024-02-01
### What's changed

* Improve Sphinx docs highlighting using RST markup by @disrupted in [#443](https://github.com/bakdata/kpops/pull/443)

* Refactor enrichment using Pydantic model validator by @disrupted in [#444](https://github.com/bakdata/kpops/pull/444)

* Refactor pipeline filter and add to public API by @disrupted in [#405](https://github.com/bakdata/kpops/pull/405)

* Bump version 3.1.0 → 3.2.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/3.1.0...3.2.0

## [3.1.0](https://github.com/bakdata/kpops/tree/3.1.0) - 2024-01-30
### What's changed

* Simplify loading of defaults by @disrupted in [#435](https://github.com/bakdata/kpops/pull/435)

* Update poetry publish workflow version to latest in [#430](https://github.com/bakdata/kpops/pull/430)

* Add support for pipeline steps parallelization by @irux in [#312](https://github.com/bakdata/kpops/pull/312)

* Add custom PascalCase to snake_case alias generator by @disrupted in [#436](https://github.com/bakdata/kpops/pull/436)

* Add parallel flag support to kpops runner by @irux in [#439](https://github.com/bakdata/kpops/pull/439)

* Bump version 3.0.2 → 3.1.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/3.0.2...3.1.0

## [3.0.2](https://github.com/bakdata/kpops/tree/3.0.2) - 2024-01-23
### What's changed

* Add step for submodule initialization on the docs by @irux in [#431](https://github.com/bakdata/kpops/pull/431)

* Add message if examples git submodule is not initialized by @disrupted in [#432](https://github.com/bakdata/kpops/pull/432)

* Update type annotation for deserialized pipeline by @disrupted in [#433](https://github.com/bakdata/kpops/pull/433)

* Fix Helm diff output by @disrupted in [#434](https://github.com/bakdata/kpops/pull/434)

* Bump version 3.0.1 → 3.0.2 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/3.0.1...3.0.2

## [3.0.1](https://github.com/bakdata/kpops/tree/3.0.1) - 2024-01-19
### What's changed

* Update pydantic dependency by @sujuka99 in [#422](https://github.com/bakdata/kpops/pull/422)

* Update docs of word-count example for v3 & new folder structure by @disrupted in [#423](https://github.com/bakdata/kpops/pull/423)

* Move ATM fraud to examples repo by @disrupted in [#425](https://github.com/bakdata/kpops/pull/425)

* Fix broken doc link in [#427](https://github.com/bakdata/kpops/pull/427)

* Add warning log if SR handler is disabled but URL is set in [#428](https://github.com/bakdata/kpops/pull/428)

* Add git submodule instructions to the contributing.md in [#429](https://github.com/bakdata/kpops/pull/429)

* Bump version 3.0.0 → 3.0.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/3.0.0...3.0.1

## [3.0.0](https://github.com/bakdata/kpops/tree/3.0.0) - 2024-01-17
### What's changed

* Merge remote-tracking branch 'origin/main' into v3 by @disrupted

* Fix test by @disrupted

* Add missing HelmApp docs by @disrupted

* Replace black with ruff by @sujuka99 in [#365](https://github.com/bakdata/kpops/pull/365)

* Add toml formatter to dprint by @sujuka99 in [#386](https://github.com/bakdata/kpops/pull/386)

* Add malva to dprint by @sujuka99 in [#385](https://github.com/bakdata/kpops/pull/385)

* Merge branch 'main' of github.com:bakdata/kpops into v3

* Migrate to Pydantic v2 by @sujuka99 in [#347](https://github.com/bakdata/kpops/pull/347)

* Allow overriding config files by @sujuka99 in [#391](https://github.com/bakdata/kpops/pull/391)

* Change substitution variables separator to `.` by @sujuka99 in [#388](https://github.com/bakdata/kpops/pull/388)

* Refactor pipeline generator & representation by @disrupted in [#392](https://github.com/bakdata/kpops/pull/392)

* Define custom components module & pipeline base dir globally by @disrupted in [#387](https://github.com/bakdata/kpops/pull/387)

* Update KPOps runner with the new options in [#395](https://github.com/bakdata/kpops/pull/395)

* Add steps for KubernetesApp->HelmApp to migration guide by @disrupted

* Fix KPOps action to get package from testPyPI in [#396](https://github.com/bakdata/kpops/pull/396)

* Use hash and trim long Helm release names instead of only trimming in [#390](https://github.com/bakdata/kpops/pull/390)

* Refactor Helm `nameOverride` by @disrupted in [#397](https://github.com/bakdata/kpops/pull/397)

* Mark component type as computed Pydantic field by @disrupted in [#399](https://github.com/bakdata/kpops/pull/399)

* Fix missing component type in pipeline schema by @disrupted in [#401](https://github.com/bakdata/kpops/pull/401)

* Refactor generate template for Python API usage by @disrupted in [#380](https://github.com/bakdata/kpops/pull/380)

* Generate defaults schema by @disrupted in [#402](https://github.com/bakdata/kpops/pull/402)

* Update docs for substitution variable usage in v3 by @sujuka99 in [#409](https://github.com/bakdata/kpops/pull/409)

* Namespace substitution vars by @sujuka99 in [#408](https://github.com/bakdata/kpops/pull/408)

* Support multiple inheritance for doc generation by @sujuka99 in [#406](https://github.com/bakdata/kpops/pull/406)

* Refactor streams-bootstrap cleanup jobs as individual HelmApp by @disrupted in [#398](https://github.com/bakdata/kpops/pull/398)

* Update docs for v3 by @sujuka99 in [#416](https://github.com/bakdata/kpops/pull/416)

* Refactor Kafka Connector resetter as individual HelmApp by @disrupted in [#400](https://github.com/bakdata/kpops/pull/400)

* Update tests resources by @sujuka99 in [#417](https://github.com/bakdata/kpops/pull/417)

* Fix enrichment of nested Pydantic BaseModel by @disrupted in [#415](https://github.com/bakdata/kpops/pull/415)

* Summarize all breaking changes in diffs at the top of the migration guide by @sujuka99 in [#419](https://github.com/bakdata/kpops/pull/419)

* Fix wrong Helm release name character limit by @disrupted in [#418](https://github.com/bakdata/kpops/pull/418)

* KPOps 3.0 by @disrupted in [#420](https://github.com/bakdata/kpops/pull/420)

* Update release workflow template to support custom changelog file path by @disrupted in [#421](https://github.com/bakdata/kpops/pull/421)

* Bump version 2.0.11 → 3.0.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/2.0.11...3.0.0

## [2.0.11](https://github.com/bakdata/kpops/tree/2.0.11) - 2023-10-24
### What's changed

* Merge remote-tracking branch 'origin/main' into v3 by @disrupted

* Create HelmApp component by @disrupted in [#370](https://github.com/bakdata/kpops/pull/370)

* Fix early exit upon Helm exit code 1 (#376) by @sujuka99

* Migrate deprecated mkdocs-material-extensions (#378) by @disrupted

* Fix docs setup page list indentation (#377) by @sujuka99

* Exclude resources from docs search (#371) by @disrupted

* Bump version 2.0.10 → 2.0.11 by @bakdata-bot

* Fix early exit upon Helm exit code 1 by @sujuka99 in [#376](https://github.com/bakdata/kpops/pull/376)

* Migrate deprecated mkdocs-material-extensions by @disrupted in [#378](https://github.com/bakdata/kpops/pull/378)

* Fix docs setup page list indentation by @sujuka99 in [#377](https://github.com/bakdata/kpops/pull/377)

* Exclude resources from docs search by @disrupted in [#371](https://github.com/bakdata/kpops/pull/371)

* Bump version 2.0.10 → 2.0.11 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/2.0.10...2.0.11

## [2.0.10](https://github.com/bakdata/kpops/tree/2.0.10) - 2023-10-12
### What's changed

* Fix environment variables documentation generation by @sujuka99 in [#362](https://github.com/bakdata/kpops/pull/362)

* Merge branch 'main' of github.com:bakdata/kpops into v3

* Make Kafka REST Proxy & Kafka Connect hosts default and improve Schema Registry config in [#354](https://github.com/bakdata/kpops/pull/354)

* Introduce ruff by @sujuka99 in [#363](https://github.com/bakdata/kpops/pull/363)

* Print details on connector name mismatch error by @disrupted in [#369](https://github.com/bakdata/kpops/pull/369)

* Enable transparent OS environment lookups from internal environment by @disrupted in [#368](https://github.com/bakdata/kpops/pull/368)

* Bump version 2.0.9 → 2.0.10 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/2.0.9...2.0.10

## [2.0.9](https://github.com/bakdata/kpops/tree/2.0.9) - 2023-09-19
### What's changed

* Move GitHub action to repository root by @disrupted in [#356](https://github.com/bakdata/kpops/pull/356)

* Fix link to kpops-examples by @sujuka99 in [#357](https://github.com/bakdata/kpops/pull/357)

* Fix Kafka connect config name for deletion in [#361](https://github.com/bakdata/kpops/pull/361)

* Bump version 2.0.8 → 2.0.9 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/2.0.8...2.0.9

## [2.0.8](https://github.com/bakdata/kpops/tree/2.0.8) - 2023-09-06
### What's changed

* Refactor component prefix & name by @disrupted in [#326](https://github.com/bakdata/kpops/pull/326)

* Remove unnecessary condition during inflate by @disrupted in [#328](https://github.com/bakdata/kpops/pull/328)

* Fix config.yaml overriding environment variables by @sujuka99 in [#353](https://github.com/bakdata/kpops/pull/353)

* Bump version 2.0.7 → 2.0.8 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/2.0.7...2.0.8

## [2.0.7](https://github.com/bakdata/kpops/tree/2.0.7) - 2023-08-31
### What's changed

* Print only rendered templates when `--template` flag is set in [#350](https://github.com/bakdata/kpops/pull/350)

* Add migration guide in [#352](https://github.com/bakdata/kpops/pull/352)

* Bump version 2.0.6 → 2.0.7 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/2.0.6...2.0.7

## [2.0.6](https://github.com/bakdata/kpops/tree/2.0.6) - 2023-08-30
### What's changed

* Simplify deployment with local Helm charts in [#349](https://github.com/bakdata/kpops/pull/349)

* Bump version 2.0.5 → 2.0.6 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/2.0.5...2.0.6

## [2.0.5](https://github.com/bakdata/kpops/tree/2.0.5) - 2023-08-30
### What's changed

* Fix versioning of docs when releasing in [#346](https://github.com/bakdata/kpops/pull/346)

* Bump version 2.0.4 → 2.0.5 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/2.0.4...2.0.5

## [2.0.4](https://github.com/bakdata/kpops/tree/2.0.4) - 2023-08-29
### What's changed

* Exclude abstract components from pipeline schema by @disrupted in [#332](https://github.com/bakdata/kpops/pull/332)

* Add `dprint` as the markdown formatter in [#337](https://github.com/bakdata/kpops/pull/337)

* Publish pre-release docs for PRs & main branch in [#339](https://github.com/bakdata/kpops/pull/339)

* Fix GitHub ref variable for pushing docs to main branch in [#343](https://github.com/bakdata/kpops/pull/343)

* Align docs colours in [#345](https://github.com/bakdata/kpops/pull/345)

* Bump version 2.0.3 → 2.0.4 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/2.0.3...2.0.4

## [2.0.3](https://github.com/bakdata/kpops/tree/2.0.3) - 2023-08-24
### What's changed

* Lint GitHub action by @disrupted in [#342](https://github.com/bakdata/kpops/pull/342)

* Fix GitHub action error in non-Python projects by @disrupted in [#340](https://github.com/bakdata/kpops/pull/340)

* Bump version 2.0.2 → 2.0.3 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/2.0.2...2.0.3

## [2.0.2](https://github.com/bakdata/kpops/tree/2.0.2) - 2023-08-23
### What's changed

* Add version dropdown to the documentation in [#336](https://github.com/bakdata/kpops/pull/336)

* Break the documentation down into smaller subsection in [#329](https://github.com/bakdata/kpops/pull/329)

* Bump version 2.0.1 → 2.0.2 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/2.0.1...2.0.2

## [2.0.1](https://github.com/bakdata/kpops/tree/2.0.1) - 2023-08-22
### What's changed

* Fix optional flags in GitHub action by @disrupted in [#334](https://github.com/bakdata/kpops/pull/334)

* Bump version 2.0.0 → 2.0.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/2.0.0...2.0.1

## [2.0.0](https://github.com/bakdata/kpops/tree/2.0.0) - 2023-08-17
### What's changed

* Merge remote-tracking branch 'origin/main' into v2 by @disrupted

* v2 by @disrupted in [#321](https://github.com/bakdata/kpops/pull/321)

* Bump version 1.7.2 → 2.0.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.7.2...2.0.0

## [1.7.2](https://github.com/bakdata/kpops/tree/1.7.2) - 2023-08-16
### What's changed

* Merge remote-tracking branch 'origin/main' into v2 by @disrupted

* Refactor input/output types by @sujuka99 in [#232](https://github.com/bakdata/kpops/pull/232)

* Fix editor integration example in docs by @sujuka99 in [#273](https://github.com/bakdata/kpops/pull/273)

* Add KPOps Runner GitHub Action to the documentation in [#325](https://github.com/bakdata/kpops/pull/325)

* Refactor Kafka Connect handler by @disrupted in [#322](https://github.com/bakdata/kpops/pull/322)

* Remove `:type` and `:rtype` from docstrings in [#324](https://github.com/bakdata/kpops/pull/324)

* Merge remote-tracking branch 'origin/main' into v2 by @disrupted

* Bump version 1.7.1 → 1.7.2 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.7.1...1.7.2

## [1.7.1](https://github.com/bakdata/kpops/tree/1.7.1) - 2023-08-15
### What's changed

* Modularize and autogenerate examples for the documentation by @sujuka99 in [#267](https://github.com/bakdata/kpops/pull/267)

* Update the variable documentation by @sujuka99 in [#266](https://github.com/bakdata/kpops/pull/266)

* Merge remote-tracking branch 'origin/main' into v2 by @disrupted

* Update docs generation by @disrupted

* Bump version 1.7.0 → 1.7.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.7.0...1.7.1

## [1.7.0](https://github.com/bakdata/kpops/tree/1.7.0) - 2023-08-15
### What's changed

* Add flag to exclude pipeline steps in [#300](https://github.com/bakdata/kpops/pull/300)

* Bump version 1.6.0 → 1.7.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.6.0...1.7.0

## [1.6.0](https://github.com/bakdata/kpops/tree/1.6.0) - 2023-08-10
### What's changed

* Refactor handling of Helm flags by @disrupted in [#319](https://github.com/bakdata/kpops/pull/319)

* Bump version 1.5.0 → 1.6.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.5.0...1.6.0

## [1.5.0](https://github.com/bakdata/kpops/tree/1.5.0) - 2023-08-10
### What's changed

* Remove camel case conversion of internal models by @disrupted in [#308](https://github.com/bakdata/kpops/pull/308)

* Automatically support schema generation for custom components by @disrupted in [#307](https://github.com/bakdata/kpops/pull/307)

* Derive component type automatically from class name by @disrupted in [#309](https://github.com/bakdata/kpops/pull/309)

* Refactor Helm wrapper and add `--set-file` flag by @disrupted in [#311](https://github.com/bakdata/kpops/pull/311)

* Set default for ToSection topics by @disrupted in [#313](https://github.com/bakdata/kpops/pull/313)

* Annotate types for ToSection models mapping by @disrupted in [#315](https://github.com/bakdata/kpops/pull/315)

* Check Poetry lock file consistency by @disrupted in [#316](https://github.com/bakdata/kpops/pull/316)

* Bump version 1.4.0 → 1.5.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.4.0...1.5.0

## [1.4.0](https://github.com/bakdata/kpops/tree/1.4.0) - 2023-08-02
### What's changed

* Update Black by @disrupted in [#294](https://github.com/bakdata/kpops/pull/294)

* Fix vulnerability in mkdocs-material by @disrupted in [#295](https://github.com/bakdata/kpops/pull/295)

* Move breaking changes section upper in the change log config in [#287](https://github.com/bakdata/kpops/pull/287)

* Order PipelineComponent fields by @disrupted in [#290](https://github.com/bakdata/kpops/pull/290)

* Migrate requests to httpx by @irux in [#302](https://github.com/bakdata/kpops/pull/302)

* Validate unique step names by @disrupted in [#292](https://github.com/bakdata/kpops/pull/292)

* Refactor CLI using dtyper by @disrupted in [#306](https://github.com/bakdata/kpops/pull/306)

* Bump version 1.3.2 → 1.4.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.3.2...1.4.0

## [1.3.2](https://github.com/bakdata/kpops/tree/1.3.2) - 2023-07-13
### What's changed

* Exclude Helm tests from dry-run diff in [#293](https://github.com/bakdata/kpops/pull/293)

* Bump version 1.3.1 → 1.3.2 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.3.1...1.3.2

## [1.3.1](https://github.com/bakdata/kpops/tree/1.3.1) - 2023-07-11
### What's changed

* Update codeowners by @disrupted in [#281](https://github.com/bakdata/kpops/pull/281)

* Reactivate Windows CI by @irux in [#255](https://github.com/bakdata/kpops/pull/255)

* Downgrade Poetry version on the Windows CI pipeline by @irux in [#286](https://github.com/bakdata/kpops/pull/286)

* Remove workaround for pipeline steps by @disrupted in [#276](https://github.com/bakdata/kpops/pull/276)

* Set ANSI theme for output of `kpops generate` by @disrupted in [#289](https://github.com/bakdata/kpops/pull/289)

* Bump version 1.3.0 → 1.3.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.3.0...1.3.1

## [1.3.0](https://github.com/bakdata/kpops/tree/1.3.0) - 2023-07-07
### What's changed

* Update KPOps runner readme for dev versions in [#279](https://github.com/bakdata/kpops/pull/279)

* Add breaking changes section to change log config in [#280](https://github.com/bakdata/kpops/pull/280)

* Plural broker field in pipeline config in [#278](https://github.com/bakdata/kpops/pull/278)

* Bump version 1.2.4 → 1.3.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.2.4...1.3.0

## [1.2.4](https://github.com/bakdata/kpops/tree/1.2.4) - 2023-06-27
### What's changed

* Update changelog action to contain miscellaneous PRs in [#269](https://github.com/bakdata/kpops/pull/269)

* Bump version 1.2.3 → 1.2.4 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.2.3...1.2.4

## [1.2.3](https://github.com/bakdata/kpops/tree/1.2.3) - 2023-06-22
### What's changed

* Refactor custom component validation & hide field from kpops output by @disrupted in [#265](https://github.com/bakdata/kpops/pull/265)

* Bump version 1.2.2 → 1.2.3 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.2.2...1.2.3

## [1.2.2](https://github.com/bakdata/kpops/tree/1.2.2) - 2023-06-21
### What's changed

* Create workflow to lint CI by @disrupted in [#260](https://github.com/bakdata/kpops/pull/260)

* Fix update docs when releasing by @irux in [#261](https://github.com/bakdata/kpops/pull/261)

* Rename change log message for uncategorized issues in [#262](https://github.com/bakdata/kpops/pull/262)

* Bump version 1.2.1 → 1.2.2 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.2.1...1.2.2

## [1.2.1](https://github.com/bakdata/kpops/tree/1.2.1) - 2023-06-21
### What's changed

* Fix update docs in release workflow by @irux in [#258](https://github.com/bakdata/kpops/pull/258)

* Bump version 1.2.0 → 1.2.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.2.0...1.2.1

## [1.2.0](https://github.com/bakdata/kpops/tree/1.2.0) - 2023-06-21
### What's changed

* Add background to docs home page by @disrupted in [#236](https://github.com/bakdata/kpops/pull/236)

* Remove enable option from helm diff in [#235](https://github.com/bakdata/kpops/pull/235)

* add --namespace option to Helm template command in [#237](https://github.com/bakdata/kpops/pull/237)

* Add missing type annotation for Pydantic attributes by @disrupted in [#238](https://github.com/bakdata/kpops/pull/238)

* Add `helm repo update <repo-name>` for Helm >3.7 in [#239](https://github.com/bakdata/kpops/pull/239)

* Fix helm version check by @sujuka99 in [#242](https://github.com/bakdata/kpops/pull/242)

* Refactor variable substitution by @sujuka99 in [#198](https://github.com/bakdata/kpops/pull/198)

* Fix Helm Version Check by @sujuka99 in [#244](https://github.com/bakdata/kpops/pull/244)

* Update Poetry version in CI by @sujuka99 in [#247](https://github.com/bakdata/kpops/pull/247)

* Add pip cache in KPOps runner action in [#249](https://github.com/bakdata/kpops/pull/249)

* Check types using Pyright by @disrupted in [#251](https://github.com/bakdata/kpops/pull/251)

* Remove MyPy by @disrupted in [#252](https://github.com/bakdata/kpops/pull/252)

* Disable broken Windows CI temporarily by @sujuka99 in [#253](https://github.com/bakdata/kpops/pull/253)

* Update release and publish workflows by @irux in [#254](https://github.com/bakdata/kpops/pull/254)

* Fix import from external module by @disrupted in [#256](https://github.com/bakdata/kpops/pull/256)

* Fix release & publish workflows by @irux in [#257](https://github.com/bakdata/kpops/pull/257)

* Bump version 1.1.5 → 1.2.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.1.5...1.2.0

## [1.1.5](https://github.com/bakdata/kpops/tree/1.1.5) - 2023-06-07
### What's changed

* Fix links to ATM-fraud defaults by @sujuka99 in [#219](https://github.com/bakdata/kpops/pull/219)

* Exclude pytest snapshots from pre-commit hook by @sujuka99 in [#226](https://github.com/bakdata/kpops/pull/226)

* Add Windows support by @irux in [#217](https://github.com/bakdata/kpops/pull/217)

* Fix missing extra input topics by @disrupted in [#230](https://github.com/bakdata/kpops/pull/230)

* Bump version 1.1.4 → 1.1.5 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.1.4...1.1.5

## [1.1.4](https://github.com/bakdata/kpops/tree/1.1.4) - 2023-05-22
### What's changed

* Document environment-specific pipeline definitions by @sujuka99 in [#210](https://github.com/bakdata/kpops/pull/210)

* Set up Helm inside composite action & install latest KPOps by default by @disrupted in [#211](https://github.com/bakdata/kpops/pull/211)

* Update example pipeline by @sujuka99 in [#216](https://github.com/bakdata/kpops/pull/216)

* Bump version 1.1.3 → 1.1.4 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.1.3...1.1.4

## [1.1.3](https://github.com/bakdata/kpops/tree/1.1.3) - 2023-05-04
### What's changed

* Rewrite bash pre-commit hooks in Python by @sujuka99 in [#207](https://github.com/bakdata/kpops/pull/207)

* Collapse pip install output for GitHub action by @disrupted in [#209](https://github.com/bakdata/kpops/pull/209)

* Fix misleading error of 'File or directory not found' by @irux in [#208](https://github.com/bakdata/kpops/pull/208)

* Bump version 1.1.2 → 1.1.3 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.1.2...1.1.3

## [1.1.2](https://github.com/bakdata/kpops/tree/1.1.2) - 2023-04-27
### What's changed

* Add titles and descriptions to Pydantic model fields by @sujuka99 in [#191](https://github.com/bakdata/kpops/pull/191)

* Respect object docstring titles by @sujuka99 in [#196](https://github.com/bakdata/kpops/pull/196)

* Allow manually running the CI by @sujuka99 in [#204](https://github.com/bakdata/kpops/pull/204)

* Generate schema in CI by @sujuka99 in [#197](https://github.com/bakdata/kpops/pull/197)

* Add `kpops --version` command by @disrupted in [#206](https://github.com/bakdata/kpops/pull/206)

* Bump version 1.1.1 → 1.1.2 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.1.1...1.1.2

## [1.1.1](https://github.com/bakdata/kpops/tree/1.1.1) - 2023-04-17
### What's changed

* Expose pipeline component by @irux in [#192](https://github.com/bakdata/kpops/pull/192)

* Bump version 1.1.0 → 1.1.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.1.0...1.1.1

## [1.1.0](https://github.com/bakdata/kpops/tree/1.1.0) - 2023-04-11
### What's changed

* Error when running generate with --steps by @sujuka99 in [#169](https://github.com/bakdata/kpops/pull/169)

* Make schema generation a builtin CLI command by @sujuka99 in [#166](https://github.com/bakdata/kpops/pull/166)

* Add CLI Usage doc generation to CI by @sujuka99 in [#174](https://github.com/bakdata/kpops/pull/174)

* Add new badges to readme and improve KubernetesApp docs in [#186](https://github.com/bakdata/kpops/pull/186)

* Read from component by @disrupted in [#193](https://github.com/bakdata/kpops/pull/193)

* Bump version 1.0.1 → 1.1.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.0.1...1.1.0

## [1.0.1](https://github.com/bakdata/kpops/tree/1.0.1) - 2023-03-23
### What's changed

* fix(README): documentation leads to user-guide by @sujuka99 in [#163](https://github.com/bakdata/kpops/pull/163)

* Fix serialization of `pathlib.Path` type on model export by @disrupted in [#168](https://github.com/bakdata/kpops/pull/168)

* Bump version 1.0.0 → 1.0.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/1.0.0...1.0.1

## [1.0.0](https://github.com/bakdata/kpops/tree/1.0.0) - 2023-03-20
### What's changed

* Update "What is KPOps" section to be more catchy by @sujuka99 in [#148](https://github.com/bakdata/kpops/pull/148)

* Fix broken links in README in [#160](https://github.com/bakdata/kpops/pull/160)

* Update CLI usage Reference by @sujuka99 in [#152](https://github.com/bakdata/kpops/pull/152)

* Fix config.yaml `defaults_path` being overridden by CLI by @sujuka99 in [#151](https://github.com/bakdata/kpops/pull/151)

* Bump version 0.12.0 → 1.0.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/0.12.0...1.0.0

## [0.12.0](https://github.com/bakdata/kpops/tree/0.12.0) - 2023-03-15
### What's changed

* Create documentation for defaults.yaml by @sujuka99 in [#146](https://github.com/bakdata/kpops/pull/146)

* Rename `kafka-connect` to `kafka-connector` by @sujuka99 in [#150](https://github.com/bakdata/kpops/pull/150)

* Set schema for Kafka Connect config by @disrupted in [#132](https://github.com/bakdata/kpops/pull/132)

* Fix missing enum keys in Kafka REST proxy response model by @irux in [#135](https://github.com/bakdata/kpops/pull/135)

* Bump version 0.11.2 → 0.12.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/0.11.2...0.12.0

## [0.11.2](https://github.com/bakdata/kpops/tree/0.11.2) - 2023-03-07
### What's changed

* Create documentation of KPOps components by @sujuka99 in [#112](https://github.com/bakdata/kpops/pull/112)

* Helm diff should not render NOTES.txt by @sujuka99 in [#130](https://github.com/bakdata/kpops/pull/130)

* Improve inflate example & enum comparison in test by @disrupted in [#104](https://github.com/bakdata/kpops/pull/104)

* Remove duplicate documentation about CLI environment variables by @disrupted in [#140](https://github.com/bakdata/kpops/pull/140)

* Provide documentation for editor integration by @sujuka99 in [#137](https://github.com/bakdata/kpops/pull/137)

* Create documentation of `config.yaml` by @sujuka99 in [#138](https://github.com/bakdata/kpops/pull/138)

* Refactor loading of component defaults to independent function by @disrupted in [#147](https://github.com/bakdata/kpops/pull/147)

* Bump version 0.11.1 → 0.11.2 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/0.11.1...0.11.2

## [0.11.1](https://github.com/bakdata/kpops/tree/0.11.1) - 2023-02-23
### What's changed

* Skip FromSection for producers by @disrupted in [#125](https://github.com/bakdata/kpops/pull/125)

* Fix pipeline environment override by @disrupted in [#127](https://github.com/bakdata/kpops/pull/127)

* Bump version 0.11.0 → 0.11.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/0.11.0...0.11.1

## [0.11.0](https://github.com/bakdata/kpops/tree/0.11.0) - 2023-02-22
### What's changed

* Bump version 0.10.4 → 0.11.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/0.10.4...0.11.0

## [0.10.4](https://github.com/bakdata/kpops/tree/0.10.4) - 2023-02-22
### What's changed

* Fix enrichment of inflated components by @disrupted in [#118](https://github.com/bakdata/kpops/pull/118)

* Assign default reviewers through codeowners by @disrupted in [#124](https://github.com/bakdata/kpops/pull/124)

* Update streams-bootstrap autoscaling config by @disrupted in [#122](https://github.com/bakdata/kpops/pull/122)

* Bump version 0.10.3 → 0.10.4 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/0.10.3...0.10.4

## [0.10.3](https://github.com/bakdata/kpops/tree/0.10.3) - 2023-02-16
### What's changed

* Update screenshot of word count pipeline by @disrupted in [#116](https://github.com/bakdata/kpops/pull/116)

* Fix topic name substitution of `${component_name}` in ToSection by @disrupted in [#117](https://github.com/bakdata/kpops/pull/117)

* Bump version 0.10.2 → 0.10.3 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/0.10.2...0.10.3

## [0.10.2](https://github.com/bakdata/kpops/tree/0.10.2) - 2023-02-15
### What's changed

* Create deployment documentation for Word Count pipeline by @sujuka99 in [#107](https://github.com/bakdata/kpops/pull/107)

* Delete leftover pipeline prefix config by @disrupted in [#111](https://github.com/bakdata/kpops/pull/111)

* Remove `poetry run` from Quickstart doc by @sujuka99 in [#114](https://github.com/bakdata/kpops/pull/114)

* Fix incomplete inflate component by @disrupted in [#105](https://github.com/bakdata/kpops/pull/105)

* Bump version 0.10.1 → 0.10.2 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/0.10.1...0.10.2

## [0.10.1](https://github.com/bakdata/kpops/tree/0.10.1) - 2023-02-13
### What's changed

* Add name to connector dry-run diff by @philipp94831 in [#108](https://github.com/bakdata/kpops/pull/108)

* Bump version 0.10.0 → 0.10.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/0.10.0...0.10.1

## [0.10.0](https://github.com/bakdata/kpops/tree/0.10.0) - 2023-02-13
### What's changed

* Fix diff not shown for new Helm releases by @disrupted in [#92](https://github.com/bakdata/kpops/pull/92)

* Fix ATM fraud example by @disrupted in [#95](https://github.com/bakdata/kpops/pull/95)

* Fix kpops version in pyproject.toml in [#99](https://github.com/bakdata/kpops/pull/99)

* Clean up dry-run logging by @philipp94831 in [#100](https://github.com/bakdata/kpops/pull/100)

* Refactor integration test by @disrupted in [#96](https://github.com/bakdata/kpops/pull/96)

* Refactor change calculation by @disrupted in [#88](https://github.com/bakdata/kpops/pull/88)

* Support printing final Kubernetes resources with kpops generate by @sujuka99 in [#69](https://github.com/bakdata/kpops/pull/69)

* Set Kafka Connect config name from component by @irux in [#98](https://github.com/bakdata/kpops/pull/98)

* Add prefix as an option to customize by @irux in [#97](https://github.com/bakdata/kpops/pull/97)

* Bump version 0.9.0 → 0.10.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/0.9.0...0.10.0

## [0.9.0](https://github.com/bakdata/kpops/tree/0.9.0) - 2023-02-03
### What's changed

* Remove mike set-default command in [#86](https://github.com/bakdata/kpops/pull/86)

* Add --create-namespace option to helm in [#91](https://github.com/bakdata/kpops/pull/91)


**Full Changelog**: https://github.com/bakdata/kpops/compare/0.8.3...0.9.0

## [0.8.3](https://github.com/bakdata/kpops/tree/0.8.3) - 2023-02-01
### What's changed

* Correct push flag of mike in [#84](https://github.com/bakdata/kpops/pull/84)

* Bump version 0.8.2 → 0.8.3 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/0.8.2...0.8.3

## [0.8.2](https://github.com/bakdata/kpops/tree/0.8.2) - 2023-02-01
### What's changed

* Add `--push` flag to mike in [#83](https://github.com/bakdata/kpops/pull/83)

* Bump version 0.8.1 → 0.8.2 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/0.8.1...0.8.2

## [0.8.1](https://github.com/bakdata/kpops/tree/0.8.1) - 2023-02-01
### What's changed

* Tidy user guide by @disrupted in [#81](https://github.com/bakdata/kpops/pull/81)

* Fix typo and metrics replication factor in Kafka values by @yannick-roeder in [#82](https://github.com/bakdata/kpops/pull/82)

* Bump version 0.8.0 → 0.8.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/0.8.0...0.8.1

## [0.8.0](https://github.com/bakdata/kpops/tree/0.8.0) - 2023-01-30
### What's changed

* Generate schema for pipeline.yaml and config.yaml by @disrupted in [#70](https://github.com/bakdata/kpops/pull/70)

* Bump version 0.7.0 → 0.8.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/0.7.0...0.8.0

## [0.7.0](https://github.com/bakdata/kpops/tree/0.7.0) - 2023-01-19
### What's changed

* Update setup.cfg by @sujuka99 in [#65](https://github.com/bakdata/kpops/pull/65)

* Refactor component configs in [#63](https://github.com/bakdata/kpops/pull/63)

* Bump version 0.6.1 → 0.7.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/0.6.1...0.7.0

## [0.6.1](https://github.com/bakdata/kpops/tree/0.6.1) - 2023-01-12
### What's changed

* Refactor Kubernetes app properties by @disrupted in [#60](https://github.com/bakdata/kpops/pull/60)

* Fix Helm release name trimming of cleanup jobs by @disrupted in [#61](https://github.com/bakdata/kpops/pull/61)

* Bump version 0.6.0 → 0.6.1 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/0.6.0...0.6.1

## [0.6.0](https://github.com/bakdata/kpops/tree/0.6.0) - 2023-01-09
### What's changed

* Separate clean, reset, and destroy logic in [#57](https://github.com/bakdata/kpops/pull/57)

* Fix trigger CI job once on release workflow in [#58](https://github.com/bakdata/kpops/pull/58)

* Fix double push of docs to GitHub pages in [#59](https://github.com/bakdata/kpops/pull/59)

* Bump version 0.5.0 → 0.6.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/0.5.0...0.6.0

## [0.5.0](https://github.com/bakdata/kpops/tree/0.5.0) - 2023-01-05
### What's changed

* Fix release version for TestPyPI by @philipp94831 in [#48](https://github.com/bakdata/kpops/pull/48)

* Change topic_name variable to output_topic_name by @MichaelKora in [#50](https://github.com/bakdata/kpops/pull/50)

* Improve exception output for integration tests by @disrupted in [#51](https://github.com/bakdata/kpops/pull/51)

* Refactor usage of Pydantic aliases by @disrupted in [#52](https://github.com/bakdata/kpops/pull/52)

* Add MyPy plugin for Pydantic by @disrupted in [#56](https://github.com/bakdata/kpops/pull/56)

* Use component name instead of type to set default output topic name by @MichaelKora in [#53](https://github.com/bakdata/kpops/pull/53)

* Refactor Helm Wrapper in [#47](https://github.com/bakdata/kpops/pull/47)

* Bump version 0.4.1 → 0.5.0 by @bakdata-bot


### New Contributors
* @MichaelKora made their first contribution in [#53](https://github.com/bakdata/kpops/pull/53)

**Full Changelog**: https://github.com/bakdata/kpops/compare/0.4.1...0.5.0

## [0.4.1](https://github.com/bakdata/kpops/tree/0.4.1) - 2022-12-22
### What's changed

* Fix link for getting started in readme by @torbsto in [#34](https://github.com/bakdata/kpops/pull/34)

* Use new Helm repositories for streams-bootstrap and Kafka Connect resetter by @philipp94831 in [#36](https://github.com/bakdata/kpops/pull/36)

* Fix spelling of PyPI by @disrupted in [#33](https://github.com/bakdata/kpops/pull/33)

* Fix typo in docs by @disrupted in [#38](https://github.com/bakdata/kpops/pull/38)

* Fix broken links in the documentation in [#39](https://github.com/bakdata/kpops/pull/39)

* Fix generate connecting to Kafka REST proxy by @disrupted in [#41](https://github.com/bakdata/kpops/pull/41)

* Bump version 0.4.0 → 0.4.1 by @bakdata-bot


### New Contributors
* @torbsto made their first contribution in [#34](https://github.com/bakdata/kpops/pull/34)

**Full Changelog**: https://github.com/bakdata/kpops/compare/0.4.0...0.4.1

## [0.4.0](https://github.com/bakdata/kpops/tree/0.4.0) - 2022-12-21
### What's changed

* Add installation instructions to README in [#30](https://github.com/bakdata/kpops/pull/30)

* Fix usage of template workflow for Poetry release by @disrupted in [#25](https://github.com/bakdata/kpops/pull/25)

* Set default value of retain clean jobs flag to false in [#31](https://github.com/bakdata/kpops/pull/31)

* Refactor component handlers by @disrupted in [#3](https://github.com/bakdata/kpops/pull/3)

* Bump version 0.3.0 → 0.3.1 by @bakdata-bot

* Bump version 0.3.1 → 0.4.0 by @bakdata-bot


**Full Changelog**: https://github.com/bakdata/kpops/compare/0.3.0...0.4.0

## [0.3.0](https://github.com/bakdata/kpops/tree/0.3.0) - 2022-12-21
### What's changed

* Initial commit by @philipp94831

* Add source code of KPOps by @raminqaf in [#1](https://github.com/bakdata/kpops/pull/1)

* Add GitHub action by @philipp94831 in [#2](https://github.com/bakdata/kpops/pull/2)

* Update project version by @raminqaf in [#4](https://github.com/bakdata/kpops/pull/4)

* Update project version by @raminqaf in [#5](https://github.com/bakdata/kpops/pull/5)

* Remove workflow and add release actions in [#8](https://github.com/bakdata/kpops/pull/8)

* Fix env variable in GitHub actions in [#9](https://github.com/bakdata/kpops/pull/9)

* Bump version 0.2.2 → 0.2.3 by @bakdata-bot

* Remove credential flag from checkout in update docs in [#10](https://github.com/bakdata/kpops/pull/10)

* Bump version 0.2.3 → 0.2.4 by @bakdata-bot

* Update version in actions readme by @jkbe in [#11](https://github.com/bakdata/kpops/pull/11)

* Bump version 0.2.4 → 0.2.5 by @bakdata-bot

* Remove push tag step in [#13](https://github.com/bakdata/kpops/pull/13)

* Bump version 0.2.5 → 0.2.6 by @bakdata-bot

* Bump version 0.2.6 → 0.3.0 by @bakdata-bot


### New Contributors
* @raminqaf made their first contribution in [#5](https://github.com/bakdata/kpops/pull/5)

<!-- generated by git-cliff -->
