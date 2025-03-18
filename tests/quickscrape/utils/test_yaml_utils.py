"""
Unit tests for the YAML utilities.

This module contains tests for the YAML serialization and deserialization
utilities in the quickscrape.utils.yaml_utils module.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

import pytest
import yaml
from _pytest.capture import CaptureFixture
from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture
from _pytest.monkeypatch import MonkeyPatch
from pytest_mock.plugin import MockerFixture
from pydantic import BaseModel

from quickscrape.utils.yaml_utils import (
    register_enum_yaml_representer,
    enum_constructor,
    yaml_safe_dump,
    yaml_safe_load,
    pydantic_model_to_yaml,
)


class TestEnum(str, Enum):
    """
    Test enum class for testing YAML serialization and deserialization.
    """
    VALUE1 = "value1"
    VALUE2 = "value2"
    VALUE3 = "value3"


class TestModel(BaseModel):
    """
    Test model class for testing Pydantic model YAML serialization.
    """
    name: str
    enum_value: TestEnum
    optional_enum: Optional[TestEnum] = None
    enum_list: List[TestEnum] = []
    nested_dict: Dict[str, Any] = {}


def test_register_enum_yaml_representer() -> None:
    """
    Test that the register_enum_yaml_representer function properly registers
    the Enum representer.
    """
    # Register the representer
    register_enum_yaml_representer()
    
    # Create a test enum value
    enum_value = TestEnum.VALUE1
    
    # Dump to YAML
    yaml_str = yaml.safe_dump(enum_value)
    
    # Check that it was serialized as a string
    assert yaml_str.startswith("value1")


def test_yaml_safe_dump_enum() -> None:
    """
    Test that yaml_safe_dump correctly handles Enum types.
    """
    # Create a test enum value
    enum_value = TestEnum.VALUE2
    
    # Dump to YAML using our utility
    yaml_str = yaml_safe_dump(enum_value)
    
    # Check that it was serialized as a string
    assert yaml_str.startswith("value2")


def test_yaml_safe_dump_dict_with_enums() -> None:
    """
    Test that yaml_safe_dump correctly handles dictionaries with Enum types.
    """
    # Create a test dictionary with enum values
    data = {
        "enum1": TestEnum.VALUE1,
        "enum2": TestEnum.VALUE2,
        "nested": {
            "enum3": TestEnum.VALUE3
        }
    }
    
    # Dump to YAML using our utility
    yaml_str = yaml_safe_dump(data)
    
    # Load the YAML back to verify
    loaded_data = yaml.safe_load(yaml_str)
    
    # Check that the enum values were serialized as strings
    assert loaded_data["enum1"] == "value1"
    assert loaded_data["enum2"] == "value2"
    assert loaded_data["nested"]["enum3"] == "value3"


def test_pydantic_model_to_yaml() -> None:
    """
    Test that pydantic_model_to_yaml correctly converts Pydantic models
    with Enum types to YAML-friendly dictionaries.
    """
    # Create a test model
    model = TestModel(
        name="test",
        enum_value=TestEnum.VALUE1,
        optional_enum=TestEnum.VALUE2,
        enum_list=[TestEnum.VALUE1, TestEnum.VALUE3],
        nested_dict={
            "key1": TestEnum.VALUE2,
            "key2": {
                "nested_key": TestEnum.VALUE3
            }
        }
    )
    
    # Convert to YAML-friendly dict
    yaml_dict = pydantic_model_to_yaml(model)
    
    # Check that all enum values were converted to strings
    assert yaml_dict["name"] == "test"
    assert yaml_dict["enum_value"] == "value1"
    assert yaml_dict["optional_enum"] == "value2"
    assert yaml_dict["enum_list"] == ["value1", "value3"]
    assert yaml_dict["nested_dict"]["key1"] == "value2"
    assert yaml_dict["nested_dict"]["key2"]["nested_key"] == "value3"
    
    # Verify that it can be serialized to YAML without errors
    yaml_str = yaml_safe_dump(yaml_dict)
    assert isinstance(yaml_str, str)
    
    # Load the YAML back to verify
    loaded_data = yaml.safe_load(yaml_str)
    assert loaded_data["enum_value"] == "value1"


def test_yaml_serialization_deserialization_round_trip() -> None:
    """
    Test a complete round trip of serialization and deserialization
    to ensure data integrity is maintained.
    """
    # Create a test model
    original_model = TestModel(
        name="round_trip_test",
        enum_value=TestEnum.VALUE1,
        optional_enum=TestEnum.VALUE2,
        enum_list=[TestEnum.VALUE1, TestEnum.VALUE3],
        nested_dict={
            "key1": TestEnum.VALUE2,
            "key2": {
                "nested_key": TestEnum.VALUE3
            }
        }
    )
    
    # Convert to YAML-friendly dict
    yaml_dict = pydantic_model_to_yaml(original_model)
    
    # Serialize to YAML
    yaml_str = yaml_safe_dump(yaml_dict)
    
    # Deserialize from YAML
    loaded_dict = yaml_safe_load(yaml_str)
    
    # Create a new model from the loaded dict
    loaded_model = TestModel(**loaded_dict)
    
    # Verify that the models are equivalent
    assert loaded_model.name == original_model.name
    assert loaded_model.enum_value == original_model.enum_value
    assert loaded_model.optional_enum == original_model.optional_enum
    assert loaded_model.enum_list == original_model.enum_list
    assert loaded_model.nested_dict["key1"] == TestEnum.VALUE2
    assert loaded_model.nested_dict["key2"]["nested_key"] == TestEnum.VALUE3 