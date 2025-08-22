from dataclasses import dataclass, field
from typing import List, Optional, Any

@dataclass
class Property:
    """Represents a property of a parameter object."""
    name: str
    type: str
    description: str
    properties: Optional[List['Property']] = field(default_factory=list)

@dataclass
class Param:
    """Represents a parameter of a function."""
    name: str
    type: str
    description: str
    position: int
    properties: Optional[List[Property]] = field(default_factory=list)

@dataclass
class FunctionSpec:
    """Represents the full specification for a function test pattern."""
    name: str
    description: str
    params: List[Param]
    return_type: str
    return_description: str

    def to_dict(self):
        """Converts the spec to a dictionary for comparison."""

        def convert_list(items):
            return [i.to_dict() if hasattr(i, 'to_dict') else i for i in items]

        return {
            "name": self.name,
            "description": self.description,
            "parameters": sorted([p.to_dict() for p in self.params], key=lambda x: x['position']),
            "return_type": self.return_type,
            "return_description": self.return_description,
        }

# Helper methods to make converting dataclasses to dicts easier
def _param_to_dict(p):
    param_dict = {
        "name": p.name,
        "description": p.description,
        "position": p.position,
        "type": p.type,
        "is_object": bool(p.properties)
    }
    if p.properties:
        param_dict["properties"] = [_prop_to_dict(prop) for prop in p.properties]
    return param_dict

def _prop_to_dict(pr):
    prop_dict = {
        "name": pr.name,
        "description": pr.description,
        "type": pr.type,
        "is_object": bool(pr.properties)
    }
    if pr.properties:
        prop_dict["properties"] = [_prop_to_dict(sub_prop) for sub_prop in pr.properties]
    return prop_dict

Param.to_dict = _param_to_dict
Property.to_dict = _prop_to_dict
