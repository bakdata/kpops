import pytest
from polyfactory.factories.pydantic_factory import ModelFactory

from kpops.api.options import FilterType
from kpops.components.base_components.models.from_section import FromSection
from kpops.components.base_components.models.to_section import ToSection
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.pipeline import Pipeline

PREFIX = "example-prefix-"


class TestComponentFactory(ModelFactory[PipelineComponent]):
    to = ToSection()
    from_ = FromSection()
    enrich = False
    validate = False


run_validation = False
test_component_1 = TestComponentFactory.build(run_validation)
test_component_2 = TestComponentFactory.build(run_validation)
test_component_3 = TestComponentFactory.build(run_validation)

test_component_1.name = "example1"
test_component_2.name = "example2"
test_component_3.name = "example3"


class TestPipeline:
    @pytest.fixture(autouse=True)
    def pipeline(self) -> Pipeline:
        pipeline = Pipeline()
        pipeline.add(test_component_1)
        pipeline.add(test_component_2)
        pipeline.add(test_component_3)
        return pipeline

    def test_filter_include(self, pipeline: Pipeline):
        predicate = FilterType.INCLUDE.create_default_step_names_filter_predicate(
            {"example2", "example3"}
        )
        pipeline.filter(predicate)
        assert len(pipeline.components) == 2
        assert test_component_2 in pipeline.components
        assert test_component_3 in pipeline.components

    def test_filter_include_empty(self, pipeline: Pipeline):
        predicate = FilterType.INCLUDE.create_default_step_names_filter_predicate(set())
        pipeline.filter(predicate)
        assert len(pipeline.components) == 0

    def test_filter_exclude(self, pipeline: Pipeline):
        predicate = FilterType.EXCLUDE.create_default_step_names_filter_predicate(
            {"example2", "example3"}
        )
        pipeline.filter(predicate)
        assert len(pipeline.components) == 1
        assert test_component_1 in pipeline.components

    def test_filter_exclude_empty(self, pipeline: Pipeline):
        predicate = FilterType.EXCLUDE.create_default_step_names_filter_predicate(set())
        pipeline.filter(predicate)
        assert len(pipeline.components) == 3
