from bpmn_print.diagram_model import (
    Condition,
    BpmnNode,
    BpmnEdge,
    BpmnDiagramModel,
)


class TestCondition:
    """Tests for Condition dataclass."""

    def test_condition_creation(self):
        """Test creating a Condition instance."""
        condition = Condition(
            number=1,
            source_name="Gateway",
            target_name="Task A",
            expression="${amount > 1000}",
        )
        assert condition.number == 1
        assert condition.source_name == "Gateway"
        assert condition.target_name == "Task A"
        assert condition.expression == "${amount > 1000}"

    def test_condition_equality(self):
        """Test that instances with same values are equal."""
        condition1 = Condition(1, "A", "B", "expr")
        condition2 = Condition(1, "A", "B", "expr")
        assert condition1 == condition2

    def test_condition_inequality(self):
        """Test that instances with different values are not equal."""
        condition1 = Condition(1, "A", "B", "expr1")
        condition2 = Condition(1, "A", "B", "expr2")
        assert condition1 != condition2


class TestBpmnNode:
    """Tests for BpmnNode dataclass."""

    def test_node_creation(self):
        """Test creating a BpmnNode instance."""
        node = BpmnNode(
            node_id="task_1", name="Process Payment", node_type="task"
        )
        assert node.node_id == "task_1"
        assert node.name == "Process Payment"
        assert node.node_type == "task"

    def test_node_with_different_types(self):
        """Test creating nodes of different types."""
        start = BpmnNode("start_1", "Start", "startEvent")
        end = BpmnNode("end_1", "End", "endEvent")
        gateway = BpmnNode("gate_1", "Decision", "exclusiveGateway")

        assert start.node_type == "startEvent"
        assert end.node_type == "endEvent"
        assert gateway.node_type == "exclusiveGateway"

    def test_node_equality(self):
        """Test that two BpmnNode instances with same values are equal."""
        node1 = BpmnNode("id1", "name", "task")
        node2 = BpmnNode("id1", "name", "task")
        assert node1 == node2


class TestBpmnEdge:
    """Tests for BpmnEdge dataclass."""

    def test_edge_creation_minimal(self):
        """Test creating a BpmnEdge with only required fields."""
        edge = BpmnEdge(source_id="node1", target_id="node2")
        assert edge.source_id == "node1"
        assert edge.target_id == "node2"
        assert edge.label is None
        assert edge.condition is None
        assert edge.condition_number is None

    def test_edge_with_label(self):
        """Test creating a BpmnEdge with a label."""
        edge = BpmnEdge(source_id="node1", target_id="node2", label="Yes")
        assert edge.label == "Yes"

    def test_edge_with_condition(self):
        """Test creating a BpmnEdge with condition and condition_number."""
        edge = BpmnEdge(
            source_id="gate1",
            target_id="task1",
            label="[1]",
            condition="${x > 5}",
            condition_number=1,
        )
        assert edge.condition == "${x > 5}"
        assert edge.condition_number == 1
        assert edge.label == "[1]"

    def test_edge_equality(self):
        """Test that two BpmnEdge instances with same values are equal."""
        edge1 = BpmnEdge("a", "b", "label", "cond", 1)
        edge2 = BpmnEdge("a", "b", "label", "cond", 1)
        assert edge1 == edge2


class TestBpmnDiagramModel:
    """Tests for BpmnDiagramModel dataclass."""

    def test_model_creation_without_conditions(self):
        """Test creating a model without any conditional edges."""
        nodes = [
            BpmnNode("start", "Start", "startEvent"),
            BpmnNode("task1", "Task 1", "task"),
            BpmnNode("end", "End", "endEvent"),
        ]
        edges = [
            BpmnEdge("start", "task1"),
            BpmnEdge("task1", "end"),
        ]
        id_to_name = {"start": "Start", "task1": "Task 1", "end": "End"}

        model = BpmnDiagramModel(nodes, edges, id_to_name)

        assert len(model.nodes) == 3
        assert len(model.edges) == 2
        assert len(model.conditions) == 0

    def test_model_creation_with_conditions(self):
        """Test that conditions are built during model initialization."""
        nodes = [
            BpmnNode("gate", "Gateway", "exclusiveGateway"),
            BpmnNode("task1", "Task 1", "task"),
            BpmnNode("task2", "Task 2", "task"),
        ]
        edges = [
            BpmnEdge("gate", "task1", "[1]", "${x > 5}", 1),
            BpmnEdge("gate", "task2", "[2]", "${x <= 5}", 2),
        ]
        id_to_name = {"gate": "Gateway", "task1": "Task 1", "task2": "Task 2"}

        model = BpmnDiagramModel(nodes, edges, id_to_name)

        assert len(model.conditions) == 2
        assert model.conditions[0].number == 1
        assert model.conditions[0].source_name == "Gateway"
        assert model.conditions[0].target_name == "Task 1"
        assert model.conditions[0].expression == "${x > 5}"

    def test_model_with_mixed_edges(self):
        """Test model with both conditional and non-conditional edges."""
        nodes = [
            BpmnNode("start", "Start", "startEvent"),
            BpmnNode("gate", "Gateway", "exclusiveGateway"),
            BpmnNode("task1", "High Value", "task"),
            BpmnNode("task2", "Low Value", "task"),
        ]
        edges = [
            BpmnEdge("start", "gate"),  # No condition
            BpmnEdge("gate", "task1", "[1]", "${amount > 1000}", 1),
            BpmnEdge("gate", "task2", "[2]", "${amount <= 1000}", 2),
        ]
        id_to_name = {
            "start": "Start",
            "gate": "Gateway",
            "task1": "High Value",
            "task2": "Low Value",
        }

        model = BpmnDiagramModel(nodes, edges, id_to_name)

        assert len(model.edges) == 3
        assert len(model.conditions) == 2  # Only conditional edges

    def test_get_conditions_returns_prebuilt_list(self):
        """Test that get_conditions returns the pre-built conditions list."""
        nodes = [BpmnNode("g", "G", "gateway")]
        edges = [BpmnEdge("g", "t", "[1]", "${x}", 1)]
        id_to_name = {"g": "G", "t": "T"}

        model = BpmnDiagramModel(nodes, edges, id_to_name)

        conditions1 = model.conditions
        conditions2 = model.conditions

        # Should return the same list object (not rebuilt)
        assert conditions1 is conditions2
        assert len(conditions1) == 1

    def test_extract_condition_from_edge_with_condition(self):
        """Test _extract_condition_from_edge with valid condition."""
        nodes = []
        edges = []
        id_to_name = {"gate": "Gateway", "task": "Task"}

        model = BpmnDiagramModel(nodes, edges, id_to_name)

        edge = BpmnEdge("gate", "task", "[1]", "${x > 0}", 1)
        condition = model._extract_condition_from_edge(edge)

        assert condition is not None
        assert condition.number == 1
        assert condition.source_name == "Gateway"
        assert condition.target_name == "Task"
        assert condition.expression == "${x > 0}"

    def test_extract_condition_from_edge_without_condition(self):
        """Test _extract_condition_from_edge with no condition."""
        model = BpmnDiagramModel([], [], {})

        edge = BpmnEdge("a", "b")
        condition = model._extract_condition_from_edge(edge)

        assert condition is None

    def test_extract_condition_from_edge_missing_condition_number(self):
        """Test _extract_condition_from_edge with condition but no number."""
        model = BpmnDiagramModel([], [], {})

        edge = BpmnEdge("a", "b", condition="${x}")
        condition = model._extract_condition_from_edge(edge)

        assert condition is None

    def test_extract_condition_from_edge_missing_condition_text(self):
        """Test _extract_condition_from_edge with number but no condition."""
        model = BpmnDiagramModel([], [], {})

        edge = BpmnEdge("a", "b", condition_number=1)
        condition = model._extract_condition_from_edge(edge)

        assert condition is None

    def test_extract_condition_uses_id_as_fallback(self):
        """Test that uses IDs when names not found."""
        model = BpmnDiagramModel([], [], {})  # Empty id_to_name

        edge = BpmnEdge("gate_id", "task_id", "[1]", "${x}", 1)
        condition = model._extract_condition_from_edge(edge)

        assert condition is not None
        assert condition.source_name == "gate_id"
        assert condition.target_name == "task_id"

    def test_build_conditions_processes_all_edges(self):
        """Test that _build_conditions processes all edges correctly."""
        edges = [
            BpmnEdge("a", "b"),  # No condition
            BpmnEdge("b", "c", "[1]", "${x}", 1),  # Condition
            BpmnEdge("b", "d", "Yes"),  # Label but no condition
            BpmnEdge("c", "e", "[2]", "${y}", 2),  # Condition
        ]
        id_to_name = {"a": "A", "b": "B", "c": "C", "d": "D", "e": "E"}

        model = BpmnDiagramModel([], edges, id_to_name)
        conditions = model._build_conditions()

        assert len(conditions) == 2
        assert conditions[0].number == 1
        assert conditions[1].number == 2

    def test_conditions_built_in_post_init(self):
        """Test that conditions are automatically built in __post_init__."""
        edges = [BpmnEdge("a", "b", "[1]", "${x}", 1)]
        id_to_name = {"a": "A", "b": "B"}

        model = BpmnDiagramModel([], edges, id_to_name)

        # Conditions should already be built without calling get_conditions
        assert hasattr(model, "conditions")
        assert len(model.conditions) == 1

    def test_model_with_empty_data(self):
        """Test creating a model with empty nodes and edges."""
        model = BpmnDiagramModel([], [], {})

        assert len(model.nodes) == 0
        assert len(model.edges) == 0
        assert len(model.conditions) == 0
        assert model.conditions == []

    def test_multiple_conditions_ordered_by_number(self):
        """Test that multiple conditions maintain their numbering order."""
        edges = [
            BpmnEdge("g", "t1", "[1]", "${x > 10}", 1),
            BpmnEdge("g", "t2", "[2]", "${x > 5 && x <= 10}", 2),
            BpmnEdge("g", "t3", "[3]", "${x <= 5}", 3),
        ]
        id_to_name = {"g": "Gateway", "t1": "T1", "t2": "T2", "t3": "T3"}

        model = BpmnDiagramModel([], edges, id_to_name)

        assert len(model.conditions) == 3
        assert model.conditions[0].number == 1
        assert model.conditions[1].number == 2
        assert model.conditions[2].number == 3
