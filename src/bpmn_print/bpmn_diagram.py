import warnings
from typing import List, Optional, Set

import graphviz

from .diagram_model import BpmnDiagramModel, BpmnEdge, BpmnNode, Condition
from .errors import BpmnRenderError
from .node_styles import NodeStyle, NODE_TYPE_CONFIG, GraphConfig
from .path_utils import prepare_output_path
from .xml_utils import BpmnContext
from .xml_constants import (
    ATTR_ID,
    ATTR_NAME,
    ATTR_SOURCE_REF,
    ATTR_TARGET_REF,
    BPMN_NS,
    XPATH_SEQUENCE_FLOW,
    XPATH_CONDITION_EXPRESSION,
)

# Condition numbering starts at 1 for user-friendly display in diagrams
CONDITION_START_NUMBER = 1


def _get_node_name(element, default_name: Optional[str], node_id: str) -> str:
    if default_name is not None:
        # Use default_name as fallback when element has no name attribute
        return element.get(ATTR_NAME, default_name)
    else:
        # Use node_id as fallback when element has no name attribute
        return element.get(ATTR_NAME, node_id)


def _create_bpmn_node(
    element, node_type: str, default_name: Optional[str]
) -> BpmnNode:
    node_id = element.get(ATTR_ID)
    name = _get_node_name(element, default_name, node_id)

    return BpmnNode(node_id=node_id, name=name, node_type=node_type)


def _extract_nodes_by_type(
    root, ns: dict, node_type: str, config: dict
) -> List[BpmnNode]:
    xpath = config["xpath"]
    default_name = config["default_name"]

    return [
        _create_bpmn_node(element, node_type, default_name)
        for element in root.findall(xpath, ns)
    ]


def _extract_all_nodes(root, ns: dict) -> List[BpmnNode]:
    nodes = []
    for node_type, config in NODE_TYPE_CONFIG.items():
        type_nodes = _extract_nodes_by_type(root, ns, node_type, config)
        nodes.extend(type_nodes)
    return nodes


def _extract_all_edges(root, ns: dict) -> List[BpmnEdge]:
    """Extract all sequence flow edges from the BPMN XML."""
    edges = []
    condition_counter = CONDITION_START_NUMBER

    # Find all sequenceFlow elements (BPMN namespace required)
    for flow in root.findall(XPATH_SEQUENCE_FLOW, ns):
        source_id = flow.get(ATTR_SOURCE_REF)
        target_id = flow.get(ATTR_TARGET_REF)
        flow_name = flow.get(ATTR_NAME, "")

        # Check for condition expression within the sequence flow
        # XPath query uses BPMN namespace
        condition_elem = flow.find(XPATH_CONDITION_EXPRESSION, ns)
        condition_text = None
        if condition_elem is not None and condition_elem.text:
            condition_text = condition_elem.text.strip()

        # Determine label and condition number
        label = None
        condition_number = None
        if condition_text:
            condition_number = condition_counter
            condition_counter += 1
            label = f"[{condition_number}]"
        elif flow_name:
            label = flow_name

        edges.append(
            BpmnEdge(
                source_id=source_id,
                target_id=target_id,
                label=label,
                condition=condition_text,
                condition_number=condition_number,
            )
        )

    return edges


def _validate_node_ids(nodes: List[BpmnNode]) -> Set[str]:
    """validate node IDs and return set of valid IDs."""
    node_ids = set()
    for node in nodes:
        if not node.node_id:
            warnings.warn(
                f"Found node with missing or empty ID: {node.name} "
                f"(type: {node.node_type})",
                UserWarning,
            )
        else:
            node_ids.add(node.node_id)
    return node_ids


def _validate_edge_references(
    edges: List[BpmnEdge], node_ids: Set[str], id_to_name: dict
):
    for edge in edges:
        if not edge.source_id:
            warnings.warn(
                "Found sequence flow with missing sourceRef", UserWarning
            )
        elif edge.source_id not in node_ids:
            source_name = id_to_name.get(edge.source_id, edge.source_id)
            warnings.warn(
                f"Sequence flow references non-existent source node: "
                f"{edge.source_id} ({source_name})",
                UserWarning,
            )

        if not edge.target_id:
            warnings.warn(
                "Found sequence flow with missing targetRef", UserWarning
            )
        elif edge.target_id not in node_ids:
            target_name = id_to_name.get(edge.target_id, edge.target_id)
            warnings.warn(
                f"Sequence flow references non-existent target node: "
                f"{edge.target_id} ({target_name})",
                UserWarning,
            )


def build_model(context: BpmnContext) -> BpmnDiagramModel:
    root = context.root
    id_to_name = context.id_to_name
    ns = BPMN_NS

    nodes = _extract_all_nodes(root, ns)
    node_ids = _validate_node_ids(nodes)
    edges = _extract_all_edges(root, ns)

    # Validate edge references
    _validate_edge_references(edges, node_ids, id_to_name)

    return BpmnDiagramModel(nodes=nodes, edges=edges, id_to_name=id_to_name)


def _create_graph() -> graphviz.Digraph:

    graph = graphviz.Digraph(format=GraphConfig.FORMAT)
    # Apply graph-level configuration
    graph.attr(rankdir=GraphConfig.RANKDIR, splines=GraphConfig.SPLINES)
    return graph


def _render_nodes(graph: graphviz.Digraph, model: BpmnDiagramModel) -> None:
    for node in model.nodes:
        config = NODE_TYPE_CONFIG[node.node_type]
        # Extract styling attributes (exclude xpath and default_name)
        style_attrs = {
            k: v
            for k, v in config.items()
            if k not in ("xpath", "default_name")
        }
        graph.node(node.node_id, node.name, **style_attrs)


def _render_edge_with_condition(
    graph: graphviz.Digraph, edge: BpmnEdge
) -> None:
    graph.edge(
        edge.source_id,
        edge.target_id,
        label=edge.label,
        fontsize=NodeStyle.CONDITION_FONT_SIZE,
        fontcolor=NodeStyle.CONDITION_FONT_COLOR,
    )


def _render_edge_with_label(graph: graphviz.Digraph, edge: BpmnEdge) -> None:
    graph.edge(
        edge.source_id,
        edge.target_id,
        label=edge.label,
        fontsize=NodeStyle.FLOW_NAME_FONT_SIZE,
    )


def _render_plain_edge(graph: graphviz.Digraph, edge: BpmnEdge) -> None:
    graph.edge(edge.source_id, edge.target_id)


def _render_edges(graph: graphviz.Digraph, model: BpmnDiagramModel) -> None:
    for edge in model.edges:
        if edge.condition:
            _render_edge_with_condition(graph, edge)
        elif edge.label:
            _render_edge_with_label(graph, edge)
        else:
            _render_plain_edge(graph, edge)


def render_model(model: BpmnDiagramModel, png_out: str) -> None:

    graph = _create_graph()
    _render_nodes(graph, model)
    _render_edges(graph, model)

    # Prepare output path (removes extension, ensures directory exists)
    output_path, _ = prepare_output_path(png_out, auto_extension=".png")

    try:
        graph.render(str(output_path), cleanup=True)
    except graphviz.ExecutableNotFound as e:
        raise BpmnRenderError.render_failed(
            png_out, "Graphviz not installed or not in PATH"
        ) from e
    except graphviz.CalledProcessError as e:
        raise BpmnRenderError.render_failed(
            png_out, f"Graphviz rendering failed: {e}"
        ) from e
    except Exception as e:
        raise BpmnRenderError.render_failed(png_out, str(e)) from e


def render(context: BpmnContext, png_out: str) -> List[Condition]:
    # Build the model from the context (pure, no Graphviz dependencies)
    model = build_model(context)

    # Render the model to PNG
    render_model(model, png_out)

    # Return conditions for backward compatibility
    return model.conditions
