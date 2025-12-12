"""Pure model classes for BPMN diagram representation.

This module contains data structures for representing BPMN diagrams
without any rendering dependencies. This allows for easy testing
and potential rendering to different formats.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple


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

    def get_conditions(self) -> List[Tuple[int, str, str, str]]:
        """Extract conditions from edges as a list of tuples.

        Returns:
            List of tuples: (number, source_name, target_name, condition)
        """
        conditions = []
        for edge in self.edges:
            if edge.condition and edge.condition_number:
                source_name = self.id_to_name.get(
                    edge.source_id,
                    edge.source_id)
                target_name = self.id_to_name.get(
                    edge.target_id,
                    edge.target_id)
                conditions.append((
                    edge.condition_number,
                    source_name,
                    target_name,
                    edge.condition
                ))
        return conditions
