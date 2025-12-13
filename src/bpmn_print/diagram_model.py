from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Condition:
    number: int
    source_name: str
    target_name: str
    expression: str


@dataclass
class BpmnNode:
    node_id: str
    name: str
    node_type: str  # Key from NODE_TYPE_CONFIG (e.g., "startEvent", "task")


@dataclass
class BpmnEdge:
    source_id: str
    target_id: str
    label: Optional[str] = None
    condition: Optional[str] = None
    condition_number: Optional[int] = None


@dataclass
class BpmnDiagramModel:

    nodes: List[BpmnNode]
    edges: List[BpmnEdge]
    id_to_name: dict  # Mapping from element IDs to names
    conditions: List[Condition] = field(default_factory=list, init=False)

    def __post_init__(self):
        self.conditions = self._build_conditions()

    def _build_conditions(self) -> List[Condition]:
        conditions = []
        for edge in self.edges:
            condition = self._extract_condition_from_edge(edge)
            if condition:
                conditions.append(condition)
        return conditions

    def _extract_condition_from_edge(
        self, edge: BpmnEdge
    ) -> Optional[Condition]:
        if not (edge.condition and edge.condition_number):
            return None

        source_name = self.id_to_name.get(edge.source_id, edge.source_id)
        target_name = self.id_to_name.get(edge.target_id, edge.target_id)

        return Condition(
            number=edge.condition_number,
            source_name=source_name,
            target_name=target_name,
            expression=edge.condition,
        )
