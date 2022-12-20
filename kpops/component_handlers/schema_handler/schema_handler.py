from __future__ import annotations

import json
import logging

from schema_registry.client import SchemaRegistryClient

from kpops.cli.exception import ClassNotFoundError
from kpops.cli.pipeline_config import PipelineConfig
from kpops.cli.registry import find_class
from kpops.component_handlers.schema_handler.schema_provider import (
    Schema,
    SchemaProvider,
)
from kpops.components.base_components.models.to_section import ToSection
from kpops.utils.colorify import greenify, magentaify, yellowify

log = logging.getLogger("SchemaHandler")


class SchemaHandler:
    _schema_provider: SchemaProvider | None = None

    def __init__(self, url: str, components_module: str | None):
        self.schema_registry_client = SchemaRegistryClient(url)
        self.components_module = components_module

    @property
    def schema_provider(self) -> SchemaProvider:
        if not self._schema_provider:
            try:
                if not self.components_module:
                    raise ValueError(
                        "The Schema Registry URL is set but you haven't specified the component module path. Please provide a valid component module path where your SchemaProvider implementation exists."
                    )
                schema_provider_class = find_class(self.components_module, SchemaProvider)  # type: ignore[type-abstract]
                self._schema_provider = schema_provider_class()
            except ClassNotFoundError:
                raise ValueError(
                    f"No schema provider found in components module {self.components_module}. "
                    f"Either implement it by inheriting from {SchemaProvider.__module__}.{SchemaProvider.__name__} and implementing its abstract method."
                )
        return self._schema_provider

    @classmethod
    def load_schema_handler(
        cls, components_module: str | None, config: PipelineConfig
    ) -> SchemaHandler | None:
        if not config.schema_registry_url:
            return None

        return cls(
            url=config.schema_registry_url,
            components_module=components_module,
        )

    def submit_schemas(self, to_section: ToSection, dry_run: bool = True) -> None:
        for topic_name, config in to_section.topics.items():
            value_schema_class = config.value_schema
            key_schema_class = config.key_schema
            if value_schema_class is not None:
                schema = self.schema_provider.provide_schema(
                    value_schema_class, to_section.models
                )
                self.__submit_value_schema(
                    schema, value_schema_class, dry_run, topic_name
                )
            if key_schema_class is not None:
                schema = self.schema_provider.provide_schema(
                    key_schema_class, to_section.models
                )
                self.__submit_key_schema(schema, key_schema_class, dry_run, topic_name)

    def delete_schemas(self, to_section: ToSection, dry_run: bool = True) -> None:
        for topic_name, config in to_section.topics.items():
            if config.value_schema is not None:
                self.__delete_subject(f"{topic_name}-value", dry_run)
            if config.key_schema is not None:
                self.__delete_subject(f"{topic_name}-key", dry_run)

    def __submit_key_schema(
        self,
        schema: Schema,
        schema_class: str,
        dry_run: bool,
        topic_name: str,
    ) -> None:
        subject = f"{topic_name}-key"
        self.__submit_schema(
            subject=subject,
            schema=schema,
            schema_class=schema_class,
            dry_run=dry_run,
        )

    def __submit_value_schema(
        self,
        schema: Schema,
        schema_class: str,
        dry_run: bool,
        topic_name: str,
    ) -> None:
        subject = f"{topic_name}-value"
        self.__submit_schema(
            subject=subject,
            schema=schema,
            schema_class=schema_class,
            dry_run=dry_run,
        )

    def __submit_schema(
        self,
        subject: str,
        schema: Schema,
        schema_class: str,
        dry_run: bool,
    ):
        if dry_run:
            if self.__subject_exists(subject):
                self.__check_compatibility(schema, schema_class, subject)
            else:
                log.info(
                    greenify(
                        f"Schema Submission: The subject {subject} will be submitted."
                    )
                )
        else:
            self.schema_registry_client.register(subject=subject, schema=schema)
            log.info(
                f"Schema Submission: schema submitted for {subject} with model {schema_class}."
            )

    def __subject_exists(self, subject: str) -> bool:
        return len(self.schema_registry_client.get_versions(subject)) > 0

    def __check_compatibility(
        self, schema: Schema, schema_class: str, subject: str
    ) -> None:
        registered_version = self.schema_registry_client.check_version(subject, schema)
        if registered_version is None:
            if not self.schema_registry_client.test_compatibility(
                subject=subject, schema=schema
            ):
                raise Exception(
                    f"Schema is not compatible for {subject} and model {schema_class}. \n {json.dumps(schema.flat_schema, indent=4)}"
                )
        else:
            log.info(
                yellowify(
                    f"Schema Submission: schema was already submitted for the subject {subject} as version {registered_version.schema}. Therefore, the specified schema must be compatible."
                )
            )

        log.info(
            f"Schema Submission: compatible schema for {subject} with model {schema_class}."
        )

    def __delete_subject(self, subject: str, dry_run: bool) -> None:
        if dry_run:
            log.info(magentaify(f"Schema Deletion: will delete subject {subject}."))
        else:
            version_list = self.schema_registry_client.delete_subject(subject)
            log.info(
                f"Schema Deletion: deleted {len(version_list)} versions for subject {subject}."
            )
