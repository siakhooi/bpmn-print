import pytest
import warnings
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from bpmn_print.bpmn_diagram import (
    _get_node_name,
    _create_bpmn_node,
    _extract_nodes_by_type,
    _extract_all_nodes,
    _extract_all_edges,
    _validate_node_ids,
    _validate_edge_references,
    build_model,
    _create_graph,
    _render_nodes,
    _render_edge_with_condition,
    _render_edge_with_label,
    _render_plain_edge,
    _render_edges,
    render_model,
    render,
    CONDITION_START_NUMBER,
)
from bpmn_print.diagram_model import BpmnNode, BpmnEdge, BpmnDiagramModel
from bpmn_print.errors import BpmnRenderError
from bpmn_print.xml_constants import BPMN_NS
from bpmn_print.xml_utils import create_bpmn_context


class TestGetNodeName:
    """Tests for _get_node_name function."""

    def test_returns_element_name_when_present(self):
        """Test that element name attribute is returned when present."""
        element = Mock()
        element.get.return_value = "Task Name"

        result = _get_node_name(element, "Default", "node_id_123")

        assert result == "Task Name"
        element.get.assert_called_once_with("name", "Default")

    def test_returns_default_name_when_element_has_no_name(self):
        """Test that default_name is used when element has no name."""
        element = Mock()
        element.get.return_value = "Default"

        result = _get_node_name(element, "Default", "node_id_123")

        assert result == "Default"

    def test_returns_node_id_when_default_is_none_and_no_name(self):
        """Test that node_id is used when default_name is None."""
        element = Mock()
        element.get.return_value = "node_id_123"

        result = _get_node_name(element, None, "node_id_123")

        assert result == "node_id_123"


class TestCreateBpmnNode:
    """Tests for _create_bpmn_node function."""

    def test_creates_node_with_all_attributes(self):
        """Test creating a BpmnNode with all attributes."""
        element = Mock()
        element.get.side_effect = lambda attr, default=None: {
            "id": "task_1",
            "name": "Process Payment",
        }.get(attr, default)

        node = _create_bpmn_node(element, "task", None)

        assert isinstance(node, BpmnNode)
        assert node.node_id == "task_1"
        assert node.name == "Process Payment"
        assert node.node_type == "task"

    def test_creates_node_with_default_name(self):
        """Test creating a node with default name."""
        element = Mock()
        element.get.side_effect = lambda attr, default=None: {
            "id": "start_1"
        }.get(attr, default)

        node = _create_bpmn_node(element, "startEvent", "Start")

        assert node.node_id == "start_1"
        assert node.name == "Start"
        assert node.node_type == "startEvent"


class TestExtractNodesByType:
    """Tests for _extract_nodes_by_type function."""

    def test_extracts_multiple_nodes(self):
        """Test extracting multiple nodes of the same type."""
        root = Mock()
        element1 = Mock()
        element1.get.side_effect = lambda attr, default=None: {
            "id": "task_1",
            "name": "Task A",
        }.get(attr, default)

        element2 = Mock()
        element2.get.side_effect = lambda attr, default=None: {
            "id": "task_2",
            "name": "Task B",
        }.get(attr, default)

        root.findall.return_value = [element1, element2]

        config = {"xpath": ".//bpmn:task", "default_name": None}
        nodes = _extract_nodes_by_type(root, BPMN_NS, "task", config)

        assert len(nodes) == 2
        assert nodes[0].node_id == "task_1"
        assert nodes[0].name == "Task A"
        assert nodes[1].node_id == "task_2"
        assert nodes[1].name == "Task B"

    def test_extracts_empty_list_when_no_nodes_found(self):
        """Test returns empty list when no nodes found."""
        root = Mock()
        root.findall.return_value = []

        config = {"xpath": ".//bpmn:task", "default_name": None}
        nodes = _extract_nodes_by_type(root, BPMN_NS, "task", config)

        assert nodes == []


class TestExtractAllNodes:
    """Tests for _extract_all_nodes function."""

    def test_extracts_nodes_from_all_types(self):
        """Test that nodes from all types are extracted."""
        root = Mock()

        # Mock different elements for different node types
        start_elem = Mock()
        start_elem.get.side_effect = lambda attr, default=None: {
            "id": "start_1"
        }.get(attr, default)

        task_elem = Mock()
        task_elem.get.side_effect = lambda attr, default=None: {
            "id": "task_1",
            "name": "Task",
        }.get(attr, default)

        end_elem = Mock()
        end_elem.get.side_effect = lambda attr, default=None: {
            "id": "end_1"
        }.get(attr, default)

        def mock_findall(xpath, ns):
            if "startEvent" in xpath:
                return [start_elem]
            elif "endEvent" in xpath:
                return [end_elem]
            elif xpath.endswith("task") or "task[" in xpath:
                return [task_elem]
            return []

        root.findall.side_effect = mock_findall

        nodes = _extract_all_nodes(root, BPMN_NS)

        assert len(nodes) >= 3
        node_ids = [n.node_id for n in nodes]
        assert "start_1" in node_ids
        assert "task_1" in node_ids
        assert "end_1" in node_ids


class TestExtractAllEdges:
    """Tests for _extract_all_edges function."""

    def test_extracts_simple_edge_without_condition(self):
        """Test extracting edge without condition."""
        root = Mock()
        flow = Mock()
        flow.get.side_effect = lambda attr, default=None: {
            "sourceRef": "task_1",
            "targetRef": "task_2",
            "name": "",
        }.get(attr, default)
        flow.find.return_value = None

        root.findall.return_value = [flow]

        edges = _extract_all_edges(root, BPMN_NS)

        assert len(edges) == 1
        assert edges[0].source_id == "task_1"
        assert edges[0].target_id == "task_2"
        assert edges[0].label is None
        assert edges[0].condition is None
        assert edges[0].condition_number is None

    def test_extracts_edge_with_name_label(self):
        """Test extracting edge with name label."""
        root = Mock()
        flow = Mock()
        flow.get.side_effect = lambda attr, default=None: {
            "sourceRef": "task_1",
            "targetRef": "task_2",
            "name": "Flow Name",
        }.get(attr, default)
        flow.find.return_value = None

        root.findall.return_value = [flow]

        edges = _extract_all_edges(root, BPMN_NS)

        assert len(edges) == 1
        assert edges[0].label == "Flow Name"
        assert edges[0].condition is None

    def test_extracts_edge_with_condition(self):
        """Test extracting edge with condition expression."""
        root = Mock()
        flow = Mock()
        flow.get.side_effect = lambda attr, default=None: {
            "sourceRef": "gateway_1",
            "targetRef": "task_1",
            "name": "",
        }.get(attr, default)

        condition_elem = Mock()
        condition_elem.text = "  ${amount > 1000}  "
        flow.find.return_value = condition_elem

        root.findall.return_value = [flow]

        edges = _extract_all_edges(root, BPMN_NS)

        assert len(edges) == 1
        assert edges[0].condition == "${amount > 1000}"
        assert edges[0].condition_number == CONDITION_START_NUMBER
        assert edges[0].label == f"[{CONDITION_START_NUMBER}]"

    def test_increments_condition_counter_for_multiple_conditions(self):
        """Test that condition numbers increment correctly."""
        root = Mock()

        flow1 = Mock()
        flow1.get.side_effect = lambda attr, default=None: {
            "sourceRef": "gateway_1",
            "targetRef": "task_1",
            "name": "",
        }.get(attr, default)
        condition_elem1 = Mock()
        condition_elem1.text = "${x > 10}"
        flow1.find.return_value = condition_elem1

        flow2 = Mock()
        flow2.get.side_effect = lambda attr, default=None: {
            "sourceRef": "gateway_1",
            "targetRef": "task_2",
            "name": "",
        }.get(attr, default)
        condition_elem2 = Mock()
        condition_elem2.text = "${x <= 10}"
        flow2.find.return_value = condition_elem2

        root.findall.return_value = [flow1, flow2]

        edges = _extract_all_edges(root, BPMN_NS)

        assert len(edges) == 2
        assert edges[0].condition_number == 1
        assert edges[0].label == "[1]"
        assert edges[1].condition_number == 2
        assert edges[1].label == "[2]"

    def test_handles_empty_condition_element(self):
        """Test that empty condition element is ignored."""
        root = Mock()
        flow = Mock()
        flow.get.side_effect = lambda attr, default=None: {
            "sourceRef": "task_1",
            "targetRef": "task_2",
            "name": "",
        }.get(attr, default)

        condition_elem = Mock()
        condition_elem.text = None
        flow.find.return_value = condition_elem

        root.findall.return_value = [flow]

        edges = _extract_all_edges(root, BPMN_NS)

        assert len(edges) == 1
        assert edges[0].condition is None
        assert edges[0].condition_number is None


class TestValidateNodeIds:
    """Tests for _validate_node_ids function."""

    def test_returns_all_valid_node_ids(self):
        """Test that all valid node IDs are returned."""
        nodes = [
            BpmnNode("task_1", "Task 1", "task"),
            BpmnNode("task_2", "Task 2", "task"),
            BpmnNode("start_1", "Start", "startEvent"),
        ]

        node_ids = _validate_node_ids(nodes)

        assert node_ids == {"task_1", "task_2", "start_1"}

    def test_warns_when_node_has_no_id(self):
        """Test that warning is issued for nodes with missing ID."""
        nodes = [
            BpmnNode("", "Task Without ID", "task"),
            BpmnNode("task_1", "Task 1", "task"),
        ]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            node_ids = _validate_node_ids(nodes)

            assert len(w) == 1
            assert "missing or empty ID" in str(w[0].message)
            assert "Task Without ID" in str(w[0].message)

        assert node_ids == {"task_1"}

    def test_handles_none_node_id(self):
        """Test handling of None as node_id."""
        nodes = [
            BpmnNode(None, "Task", "task"),
        ]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            node_ids = _validate_node_ids(nodes)

            assert len(w) == 1

        assert node_ids == set()


class TestValidateEdgeReferences:
    """Tests for _validate_edge_references function."""

    def test_no_warnings_for_valid_edges(self):
        """Test no warnings when all edge references are valid."""
        edges = [
            BpmnEdge("task_1", "task_2", None, None, None),
            BpmnEdge("task_2", "end_1", None, None, None),
        ]
        node_ids = {"task_1", "task_2", "end_1"}
        id_to_name = {}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _validate_edge_references(edges, node_ids, id_to_name)

            assert len(w) == 0

    def test_warns_when_source_id_missing(self):
        """Test warning when edge has missing sourceRef."""
        edges = [BpmnEdge("", "task_2", None, None, None)]
        node_ids = {"task_2"}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _validate_edge_references(edges, node_ids, {})

            assert len(w) == 1
            assert "missing sourceRef" in str(w[0].message)

    def test_warns_when_source_id_not_found(self):
        """Test warning when source node doesn't exist."""
        edges = [BpmnEdge("nonexistent", "task_2", None, None, None)]
        node_ids = {"task_2"}
        id_to_name = {"nonexistent": "Missing Task"}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _validate_edge_references(edges, node_ids, id_to_name)

            assert len(w) == 1
            assert "non-existent source node" in str(w[0].message)
            assert "Missing Task" in str(w[0].message)

    def test_warns_when_target_id_missing(self):
        """Test warning when edge has missing targetRef."""
        edges = [BpmnEdge("task_1", "", None, None, None)]
        node_ids = {"task_1"}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _validate_edge_references(edges, node_ids, {})

            assert len(w) == 1
            assert "missing targetRef" in str(w[0].message)

    def test_warns_when_target_id_not_found(self):
        """Test warning when target node doesn't exist."""
        edges = [BpmnEdge("task_1", "nonexistent", None, None, None)]
        node_ids = {"task_1"}
        id_to_name = {"nonexistent": "Missing Target"}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _validate_edge_references(edges, node_ids, id_to_name)

            assert len(w) == 1
            assert "non-existent target node" in str(w[0].message)
            assert "Missing Target" in str(w[0].message)


class TestBuildModel:
    """Tests for build_model function."""

    def test_builds_model_from_valid_bpmn(self):
        """Test building model from valid BPMN XML."""
        with TemporaryDirectory() as tmpdir:
            xml_file = Path(tmpdir) / "test.bpmn"
            xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL">
    <process id="Process_1">
        <startEvent id="StartEvent_1" name="Start"/>
        <task id="Task_1" name="Do Work"/>
        <endEvent id="EndEvent_1" name="End"/>
        <sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Task_1"/>
        <sequenceFlow id="Flow_2" sourceRef="Task_1" targetRef="EndEvent_1"/>
    </process>
</definitions>"""
            xml_file.write_text(xml_content)

            context = create_bpmn_context(str(xml_file))
            model = build_model(context)

            assert isinstance(model, BpmnDiagramModel)
            assert len(model.nodes) == 3
            assert len(model.edges) == 2

            node_ids = [n.node_id for n in model.nodes]
            assert "StartEvent_1" in node_ids
            assert "Task_1" in node_ids
            assert "EndEvent_1" in node_ids

    def test_model_includes_id_to_name_mapping(self):
        """Test that model includes id to name mapping."""
        with TemporaryDirectory() as tmpdir:
            xml_file = Path(tmpdir) / "test.bpmn"
            xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL">
    <process id="Process_1">
        <task id="Task_1" name="My Task"/>
    </process>
</definitions>"""
            xml_file.write_text(xml_content)

            context = create_bpmn_context(str(xml_file))
            model = build_model(context)

            assert "Task_1" in model.id_to_name
            assert model.id_to_name["Task_1"] == "My Task"


class TestCreateGraph:
    """Tests for _create_graph function."""

    def test_creates_graphviz_digraph(self):
        """Test that a Graphviz Digraph is created."""
        graph = _create_graph()

        assert graph is not None
        assert hasattr(graph, "node")
        assert hasattr(graph, "edge")
        assert hasattr(graph, "render")


class TestRenderNodes:
    """Tests for _render_nodes function."""

    def test_renders_all_nodes_to_graph(self):
        """Test that all nodes are added to graph."""
        graph = Mock()
        model = BpmnDiagramModel(
            nodes=[
                BpmnNode("task_1", "Task 1", "task"),
                BpmnNode("start_1", "Start", "startEvent"),
            ],
            edges=[],
            id_to_name={},
        )

        _render_nodes(graph, model)

        assert graph.node.call_count == 2


class TestRenderEdgeWithCondition:
    """Tests for _render_edge_with_condition function."""

    def test_renders_edge_with_condition_styling(self):
        """Test edge with condition is rendered with proper styling."""
        graph = Mock()
        edge = BpmnEdge("gateway_1", "task_1", "[1]", "${x > 10}", 1)

        _render_edge_with_condition(graph, edge)

        graph.edge.assert_called_once()
        call_args = graph.edge.call_args
        assert call_args[0][0] == "gateway_1"
        assert call_args[0][1] == "task_1"
        assert call_args[1]["label"] == "[1]"
        assert "fontsize" in call_args[1]
        assert "fontcolor" in call_args[1]


class TestRenderEdgeWithLabel:
    """Tests for _render_edge_with_label function."""

    def test_renders_edge_with_label(self):
        """Test edge with label is rendered correctly."""
        graph = Mock()
        edge = BpmnEdge("task_1", "task_2", "Next Step", None, None)

        _render_edge_with_label(graph, edge)

        graph.edge.assert_called_once()
        call_args = graph.edge.call_args
        assert call_args[0][0] == "task_1"
        assert call_args[0][1] == "task_2"
        assert call_args[1]["label"] == "Next Step"
        assert "fontsize" in call_args[1]


class TestRenderPlainEdge:
    """Tests for _render_plain_edge function."""

    def test_renders_plain_edge_without_label(self):
        """Test plain edge is rendered without label."""
        graph = Mock()
        edge = BpmnEdge("task_1", "task_2", None, None, None)

        _render_plain_edge(graph, edge)

        graph.edge.assert_called_once_with("task_1", "task_2")


class TestRenderEdges:
    """Tests for _render_edges function."""

    def test_renders_all_edge_types(self):
        """Test that all edge types are rendered correctly."""
        graph = Mock()
        model = BpmnDiagramModel(
            nodes=[],
            edges=[
                BpmnEdge("task_1", "task_2", "[1]", "${x}", 1),
                BpmnEdge("task_2", "task_3", "Label", None, None),
                BpmnEdge("task_3", "task_4", None, None, None),
            ],
            id_to_name={},
        )

        _render_edges(graph, model)

        assert graph.edge.call_count == 3


class TestRenderModel:
    """Tests for render_model function."""

    @patch("bpmn_print.bpmn_diagram._create_graph")
    @patch("bpmn_print.bpmn_diagram.prepare_output_path")
    def test_renders_model_successfully(
        self, mock_prepare_path, mock_create_graph
    ):
        """Test that model is rendered to PNG successfully."""
        mock_graph = Mock()
        mock_create_graph.return_value = mock_graph
        mock_prepare_path.return_value = (Path("/tmp/output"), ".png")

        model = BpmnDiagramModel(
            nodes=[BpmnNode("task_1", "Task", "task")], edges=[], id_to_name={}
        )

        render_model(model, "/tmp/output.png")

        mock_graph.render.assert_called_once()

    @patch("bpmn_print.bpmn_diagram._create_graph")
    @patch("bpmn_print.bpmn_diagram.prepare_output_path")
    def test_raises_error_when_graphviz_not_found(
        self, mock_prepare_path, mock_create_graph
    ):
        """Test that appropriate error is raised when Graphviz not found."""
        import graphviz

        mock_graph = Mock()
        mock_graph.render.side_effect = graphviz.ExecutableNotFound(
            "dot not found"
        )
        mock_create_graph.return_value = mock_graph
        mock_prepare_path.return_value = (Path("/tmp/output"), ".png")

        model = BpmnDiagramModel(nodes=[], edges=[], id_to_name={})

        with pytest.raises(BpmnRenderError) as exc_info:
            render_model(model, "/tmp/output.png")

        assert "Graphviz not installed" in str(exc_info.value)

    @patch("bpmn_print.bpmn_diagram._create_graph")
    @patch("bpmn_print.bpmn_diagram.prepare_output_path")
    def test_raises_error_when_rendering_fails(
        self, mock_prepare_path, mock_create_graph
    ):
        """Test that appropriate error is raised when rendering fails."""
        import graphviz

        mock_graph = Mock()
        # Create a proper CalledProcessError with correct signature:
        # CalledProcessError(returncode, cmd, output, stderr)
        mock_graph.render.side_effect = graphviz.CalledProcessError(
            1, ["dot"], "stdout", "stderr"
        )
        mock_create_graph.return_value = mock_graph
        mock_prepare_path.return_value = (Path("/tmp/output"), ".png")

        model = BpmnDiagramModel(nodes=[], edges=[], id_to_name={})

        with pytest.raises(BpmnRenderError) as exc_info:
            render_model(model, "/tmp/output.png")

        assert "Graphviz rendering failed" in str(exc_info.value)

    @patch("bpmn_print.bpmn_diagram._create_graph")
    @patch("bpmn_print.bpmn_diagram.prepare_output_path")
    def test_raises_error_for_generic_exception(
        self, mock_prepare_path, mock_create_graph
    ):
        """Test that generic exceptions are caught and wrapped in
        BpmnRenderError."""
        mock_graph = Mock()
        mock_graph.render.side_effect = RuntimeError(
            "Unexpected error occurred"
        )
        mock_create_graph.return_value = mock_graph
        mock_prepare_path.return_value = (Path("/tmp/output"), ".png")

        model = BpmnDiagramModel(nodes=[], edges=[], id_to_name={})

        with pytest.raises(BpmnRenderError) as exc_info:
            render_model(model, "/tmp/output.png")

        assert "Unexpected error occurred" in str(exc_info.value)


class TestRender:
    """Tests for render function (integration)."""

    @patch("bpmn_print.bpmn_diagram.render_model")
    @patch("bpmn_print.bpmn_diagram.build_model")
    def test_render_calls_build_and_render_model(
        self, mock_build_model, mock_render_model
    ):
        """Test that render function calls build_model and render_model."""
        mock_model = Mock()
        mock_model.conditions = []
        mock_build_model.return_value = mock_model

        conditions = render("input.bpmn", "output.png")

        mock_build_model.assert_called_once_with("input.bpmn")
        mock_render_model.assert_called_once_with(mock_model, "output.png")
        assert conditions == []

    @patch("bpmn_print.bpmn_diagram.render_model")
    @patch("bpmn_print.bpmn_diagram.build_model")
    def test_render_returns_conditions(
        self, mock_build_model, mock_render_model
    ):
        """Test that render function returns conditions from model."""
        from bpmn_print.diagram_model import Condition

        mock_model = Mock()
        mock_model.conditions = [
            Condition(1, "Gateway", "Task A", "${x > 10}"),
            Condition(2, "Gateway", "Task B", "${x <= 10}"),
        ]
        mock_build_model.return_value = mock_model

        conditions = render("input.bpmn", "output.png")

        assert len(conditions) == 2
        assert conditions[0].number == 1
        assert conditions[1].number == 2
