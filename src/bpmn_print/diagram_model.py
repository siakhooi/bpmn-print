"""Pure model classes for BPMN diagram representation.

This module contains data structures for representing BPMN diagrams
without any rendering dependencies. This allows for easy testing
and potential rendering to different formats.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Condition:
    """Represents a conditional branch in a BPMN sequence flow.

    This dataclass provides a structured representation of conditional
    branches, making it easier to work with conditions than using tuples.
    Supports tuple unpacking for backward compatibility:
        number, source_name, target_name, expression = condition_obj
    """
    number: int
    source_name: str
    target_name: str
    expression: str

    def __iter__(self):
        """Allow tuple unpacking for backward compatibility."""
        return iter((self.number, self.source_name, self.target_name,
                    self.expression))


@dataclass
class BpmnNode:
    """Represents a BPMN node in the diagram model."""
    node_id: str
    name: str
    node_type: str  # Key from NODE_TYPE_CONFIG (e.g., "startEvent", "task")


@dataclass
class BpmnEdge:
    """Represents a BPMN sequence flow edge in the diagram model."""
    source_id: str
    target_id: str
    label: Optional[str] = None
    condition: Optional[str] = None
    condition_number: Optional[int] = None


@dataclass
class BpmnDiagramModel:
    """Pure model representation of a BPMN diagram.

    This model contains all nodes and edges extracted from BPMN XML,
    without any rendering dependencies. This allows for easy testing
    and potential rendering to different formats.
    """
    nodes: List[BpmnNode]
    edges: List[BpmnEdge]
    id_to_name: dict  # Mapping from element IDs to names

    def _extract_condition_from_edge(
        self, edge: BpmnEdge
    ) -> Optional[Condition]:
        """Extract a Condition object from an edge if it has a condition.

        Helper function to convert an edge with a condition into a
        structured Condition object.

        Args:
            edge: BpmnEdge to extract condition from

        Returns:
            Condition object if edge has a condition, None otherwise
        """
        if not (edge.condition and edge.condition_number):
            return None

        source_name = self.id_to_name.get(edge.source_id, edge.source_id)
        target_name = self.id_to_name.get(edge.target_id, edge.target_id)

        return Condition(
            number=edge.condition_number,
            source_name=source_name,
            target_name=target_name,
            expression=edge.condition
        )

    def get_conditions(self) -> List[Condition]:
        """Extract conditions from edges as a list of Condition objects.

        Returns:
            List of Condition objects. Each Condition represents a
            conditional branch with its number, source, target, and
            condition expression. Supports tuple unpacking for backward
            compatibility.
        """
        conditions = []
        for edge in self.edges:
            condition = self._extract_condition_from_edge(edge)
            if condition:
                conditions.append(condition)
        return conditions
