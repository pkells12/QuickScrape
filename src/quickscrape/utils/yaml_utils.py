"""
YAML utilities for QuickScrape.

This module provides utilities for YAML serialization and deserialization,
particularly handling Pydantic enum types properly.
"""

from enum import Enum
from typing import Any, Dict, Type

import yaml
from yaml.representer import SafeRepresenter


def register_enum_yaml_representer() -> None:
    """
    Register a YAML representer for Enum types.
    
    This ensures that enum values are serialized as strings rather than complex
    Python objects, making them easier to read and deserialize.
    """
    def _enum_representer(dumper: yaml.SafeDumper, data: Enum) -> yaml.ScalarNode:
        """Represent an Enum as a scalar value."""
        return dumper.represent_scalar(f"tag:yaml.org,2002:str", str(data.value))
    
    # Register the representer for Enum types
    yaml.SafeDumper.add_multi_representer(Enum, _enum_representer)


def enum_constructor(loader: yaml.SafeLoader, node: yaml.Node, enum_class: Type[Enum]) -> Enum:
    """
    Construct an Enum value from a YAML node.
    
    Args:
        loader: YAML loader
        node: YAML node containing the enum value
        enum_class: The Enum class to instantiate
        
    Returns:
        Enum: The instantiated enum value
    """
    value = loader.construct_scalar(node)
    return enum_class(value)


def process_data_for_yaml(data: Any) -> Any:
    """
    Process data before YAML serialization to handle Enum types.
    
    Args:
        data: Data to process
        
    Returns:
        Any: Processed data safe for YAML serialization
    """
    if isinstance(data, Enum):
        return data.value
    elif isinstance(data, dict):
        return {k: process_data_for_yaml(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [process_data_for_yaml(v) for v in data]
    elif isinstance(data, tuple):
        return tuple(process_data_for_yaml(v) for v in data)
    return data


def yaml_safe_dump(data: Any, stream=None, **kwargs) -> Any:
    """
    Safely dump data to YAML, properly handling Enum types.
    
    Args:
        data: Data to dump
        stream: Optional stream to dump to
        **kwargs: Additional arguments passed to yaml.safe_dump
        
    Returns:
        Any: Result from yaml.safe_dump
    """
    # Register the representer for Enum types
    register_enum_yaml_representer()
    
    # Process data to handle Enum values
    processed_data = process_data_for_yaml(data)
    
    # Dump the processed data to YAML
    return yaml.safe_dump(processed_data, stream, **kwargs)


def yaml_safe_load(stream) -> Any:
    """
    Safely load data from YAML.
    
    Args:
        stream: Stream to load from
        
    Returns:
        Any: Loaded data
    """
    return yaml.safe_load(stream)


def pydantic_model_to_yaml(model: Any) -> Dict[str, Any]:
    """
    Convert a Pydantic model to a YAML-friendly dictionary.
    
    This function handles Enum types and nested models properly.
    
    Args:
        model: Pydantic model instance
        
    Returns:
        Dict[str, Any]: Dictionary representation suitable for YAML serialization
    """
    # Convert to dict using Pydantic's model_dump method
    model_dict = model.model_dump()
    
    # Process the dictionary to handle Enum types
    return process_data_for_yaml(model_dict) 