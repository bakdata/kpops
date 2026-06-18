from __future__ import annotations

import json
import logging
from functools import cached_property
from typing import TYPE_CHECKING, final

from schema_registry.client import AsyncSchemaRegistryClient
from schema_registry.client.schema import AvroSchema
from schema_registry.client.utils import SchemaVersion

from kpops.component_handlers.schema_handler.schema_provider import (
    Schema,
    SchemaProvider,
)
from kpops.core.exception import ClassNotFoundError
from kpops.core.registry import Registry, find_class
from kpops.utils.colorify import greenify, magentaify, yellowify

if TYPE_CHECKING:
    from kpops.components.base_components.models.to_section import ToSection
    from kpops.config import KpopsConfig

log = logging.getLogger("SchemaHandler")


@final
class SchemaHandler:
    def __init__(self, kpops_config: KpopsConfig) -> None:
        self.schema_registry_client = AsyncSchemaRegistryClient(
            str(kpops_config.schema_registry.url),
            timeout=kpops_config.schema_registry.timeout,  # pyright: ignore[reportArgumentType]
        )

    @cached_property
    def schema_provider(self) -> SchemaProvider:
        try:
            schema_provider_class = find_class(
                Registry.iter_component_modules(), base=SchemaProvider
            )
            return schema_provider_class()  # pyright: ignore[reportAbstractUsage]
        except ClassNotFoundError as e:
            msg = f"No schema provider found. Please implement the abstract method in {SchemaProvider.__module__}.{SchemaProvider.__name__}."
            raise ValueError(msg) from e

    @classmethod
    def load_schema_handler(cls, config: KpopsConfig) -> SchemaHandler | None:
        if config.schema_registry.enabled:
            return cls(config)
        if not config.schema_registry.enabled and config.schema_registry.url:
            log.warning(
                yellowify(
                    f"The property schema_registry.enabled is set to False but the URL is set to {config.schema_registry.url}."
                    f"\nIf you want to use the schema handler make sure to enable it."
                )
            )
        return None

    async def submit_schemas(self, to_section: ToSection, dry_run: bool = True) -> None:
        for topic_name, config in to_section.topics.items():
            value_schema_class = config.value_schema
            key_schema_class = config.key_schema
            if value_schema_class is not None:
                schema = self.schema_provider.provide_schema(
                    value_schema_class, to_section.models
                )
                await self.__submit_value_schema(
                    schema, value_schema_class, dry_run, topic_name
                )
            if key_schema_class is not None:
                schema = self.schema_provider.provide_schema(
                    key_schema_class, to_section.models
                )
                await self.__submit_key_schema(
                    schema, key_schema_class, dry_run, topic_name
                )

    async def delete_schemas(self, to_section: ToSection, dry_run: bool = True) -> None:
        for topic_name, config in to_section.topics.items():
            if config.value_schema is not None:
                await self.__delete_subject(f"{topic_name}-value", dry_run)
            if config.key_schema is not None:
                await self.__delete_subject(f"{topic_name}-key", dry_run)

    async def __submit_key_schema(
        self,
        schema: Schema,
        schema_class: str,
        dry_run: bool,
        topic_name: str,
    ) -> None:
        subject = f"{topic_name}-key"
        await self.__submit_schema(
            subject=subject,
            schema=schema,
            schema_class=schema_class,
            dry_run=dry_run,
        )

    async def __submit_value_schema(
        self,
        schema: Schema,
        schema_class: str,
        dry_run: bool,
        topic_name: str,
    ) -> None:
        subject = f"{topic_name}-value"
        await self.__submit_schema(
            subject=subject,
            schema=schema,
            schema_class=schema_class,
            dry_run=dry_run,
        )

    async def __submit_schema(
        self,
        subject: str,
        schema: Schema,
        schema_class: str,
        dry_run: bool,
    ):
        if dry_run:
            if await self.__subject_exists(subject):
                await self.__check_compatibility(schema, schema_class, subject)
            else:
                log.info(
                    greenify(
                        f"Schema Submission: The subject {subject} will be submitted."
                    )
                )
        else:
            await self.schema_registry_client.register(  # pyright: ignore[reportUnknownMemberType]
                subject=subject, schema=schema
            )
            log.info(
                f"Schema Submission: schema submitted for {subject} with model {schema_class}."
            )

    async def __subject_exists(self, subject: str) -> bool:
        versions: list[SchemaVersion] = await self.schema_registry_client.get_versions(  # pyright: ignore[reportUnknownMemberType]
            subject
        )
        return len(versions) > 0

    async def __check_compatibility(
        self, schema: Schema, schema_class: str, subject: str
    ) -> None:
        registered_version = await self.schema_registry_client.check_version(  # pyright: ignore[reportUnknownMemberType]
            subject, schema
        )
        if registered_version is None:
            if not await self.schema_registry_client.test_compatibility(  # pyright: ignore[reportUnknownMemberType]
                subject=subject, schema=schema
            ):
                schema_str = (
                    schema.flat_schema
                    if isinstance(schema, AvroSchema)
                    else str(schema)
                )
                msg = f"Schema is not compatible for {subject} and model {schema_class}. \n {json.dumps(schema_str, indent=4)}"
                raise Exception(msg)
        else:
            log.debug(
                f"Schema Submission: schema was already submitted for the subject {subject} as version {registered_version.schema}. Therefore, the specified schema must be compatible."  # pyright: ignore[reportUnknownMemberType]
            )

        log.info(
            f"Schema Submission: compatible schema for {subject} with model {schema_class}."
        )

    async def __delete_subject(self, subject: str, dry_run: bool) -> None:
        if dry_run:
            log.info(magentaify(f"Schema Deletion: will delete subject {subject}."))
        else:
            version_list: list[
                SchemaVersion
            ] = await self.schema_registry_client.delete_subject(subject)  # pyright: ignore[reportUnknownMemberType]
            log.info(
                f"Schema Deletion: deleted {len(version_list)} versions for subject {subject}."
            )
