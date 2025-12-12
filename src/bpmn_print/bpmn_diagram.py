import warnings
from typing import List, Optional, Set

import graphviz

from .diagram_model import (
    BpmnDiagramModel, BpmnEdge, BpmnNode, Condition
)
from .errors import BpmnRenderError
from .node_styles import (
    BPMN_NS, NodeStyle, NODE_TYPE_CONFIG, GraphConfig
)
from .path_utils import prepare_output_path
from .xml_utils import (
    parse_bpmn_xml_with_namespace, build_id_to_name_mapping
)
from .xml_constants import (
    ATTR_ID, ATTR_NAME, ATTR_SOURCE_REF, ATTR_TARGET_REF,
    XPATH_SEQUENCE_FLOW, XPATH_CONDITION_EXPRESSION
)


def _parse_bpmn_xml(xml_file: str):
    """Parse BPMN XML file and return root element and namespace mapping.

    This function parses the BPMN XML file and returns the root element
    along with the BPMN namespace mapping. The namespace mapping is required
    for all XPath queries that target BPMN elements (e.g., bpmn:startEvent,
    bpmn:sequenceFlow).

    Args:
        xml_file: Path to the BPMN XML file

    Returns:
        Tuple of (root_element, namespace_dict) where namespace_dict is
        BPMN_NS containing the BPMN namespace mapping for XPath queries.

    Raises:
        BpmnFileError: If the XML file does not exist, is not a file,
            or cannot be read
        BpmnParseError: If the XML file is malformed or invalid
    """
    return parse_bpmn_xml_with_namespace(xml_file, BPMN_NS)


def _get_node_name(element, default_name: Optional[str], node_id: str) -> str:
    """Extract and normalize the name for a BPMN node.

    This function standardizes the naming behavior across all node types:
    - If the element has a "name" attribute, use it
    - If no "name" attribute and default_name is provided (not None),
      use default_name
    - If no "name" attribute and default_name is None, use the node_id

    This ensures all nodes have a meaningful display name, even if not
    explicitly named in the BPMN XML.

    Args:
        element: XML element representing the BPMN node
        default_name: Default name to use if element has no name attribute.
            If None, falls back to node_id.
        node_id: The ID of the node (used as final fallback)

    Returns:
        The display name for the node
    """
    if default_name is not None:
        # Use default_name as fallback when element has no name attribute
        return element.get(ATTR_NAME, default_name)
    else:
        # Use node_id as fallback when element has no name attribute
        return element.get(ATTR_NAME, node_id)


def _create_bpmn_node(
    element, node_type: str, default_name: Optional[str]
) -> BpmnNode:
    """Create a BpmnNode from an XML element.

    Args:
        element: XML element representing a BPMN node
        node_type: Type of the node (e.g., "startEvent", "task")
        default_name: Default name if element has no name attribute

    Returns:
        BpmnNode instance
    """
    node_id = element.get(ATTR_ID)
    name = _get_node_name(element, default_name, node_id)

    return BpmnNode(
        node_id=node_id,
        name=name,
        node_type=node_type
    )


def _extract_nodes_by_type(
    root, ns: dict, node_type: str, config: dict
) -> List[BpmnNode]:
    """Extract all nodes of a specific type from the BPMN XML.

    Args:
        root: Root element of the BPMN XML tree
        ns: Namespace mapping for XPath queries
        node_type: Type of nodes to extract (e.g., "startEvent")
        config: Configuration dict with xpath and default_name

    Returns:
        List of BpmnNode instances for the specified type
    """
    xpath = config["xpath"]
    default_name = config["default_name"]

    return [
        _create_bpmn_node(element, node_type, default_name)
        for element in root.findall(xpath, ns)
    ]


def _extract_all_nodes(root, ns: dict) -> List[BpmnNode]:
    """Extract all BPMN nodes from the XML tree.

    This function iterates through all node types defined in NODE_TYPE_CONFIG
    and extracts nodes of each type using XPath queries with the
    BPMN namespace.

    Args:
        root: Root element of the BPMN XML tree
        ns: Namespace mapping for XPath queries

    Returns:
        List of all BpmnNode instances found in the XML
    """
    nodes = []
    for node_type, config in NODE_TYPE_CONFIG.items():
        type_nodes = _extract_nodes_by_type(root, ns, node_type, config)
        nodes.extend(type_nodes)
    return nodes


def _validate_node_ids(nodes: List[BpmnNode]) -> Set[str]:
    """Extract and validate node IDs.

    Args:
        nodes: List of BPMN nodes

    Returns:
        Set of valid node IDs

    Warns:
        UserWarning: If any node has a missing or empty ID
    """
    node_ids = set()
    for node in nodes:
        if not node.node_id:
            warnings.warn(
                f"Found node with missing or empty ID: {node.name} "
                f"(type: {node.node_type})",
                UserWarning
            )
        else:
            node_ids.add(node.node_id)
    return node_ids


def _validate_edge_references(
    edges: List[BpmnEdge], node_ids: Set[str], id_to_name: dict
):
    """Validate that edge references point to existing nodes.

    Args:
        edges: List of BPMN edges to validate
        node_ids: Set of valid node IDs
        id_to_name: Dictionary mapping element IDs to names

    Warns:
        UserWarning: If any edge references a non-existent node
    """
    for edge in edges:
        if not edge.source_id:
            warnings.warn(
                "Found sequence flow with missing sourceRef",
                UserWarning
            )
        elif edge.source_id not in node_ids:
            source_name = id_to_name.get(edge.source_id, edge.source_id)
            warnings.warn(
                f"Sequence flow references non-existent source node: "
                f"{edge.source_id} ({source_name})",
                UserWarning
            )

        if not edge.target_id:
            warnings.warn(
                "Found sequence flow with missing targetRef",
                UserWarning
            )
        elif edge.target_id not in node_ids:
            target_name = id_to_name.get(edge.target_id, edge.target_id)
            warnings.warn(
                f"Sequence flow references non-existent target node: "
                f"{edge.target_id} ({target_name})",
                UserWarning
            )


def build_model(xml_file: str) -> BpmnDiagramModel:
    """Build a pure model representation of the BPMN diagram from XML.

    This function extracts all nodes and edges from the BPMN XML file
    into a model structure without any rendering dependencies. This allows
    for easy testing and potential rendering to different formats.

    Args:
        xml_file: Path to the BPMN XML file

    Returns:
        BpmnDiagramModel containing all nodes and edges

    Raises:
        BpmnFileError: If the XML file does not exist, is not a file,
            or cannot be read
        BpmnParseError: If the XML file is malformed or invalid

    Warns:
        UserWarning: If sequence flows reference non-existent nodes or
            have missing IDs
    """
    root, ns = _parse_bpmn_xml(xml_file)
    id_to_name = build_id_to_name_mapping(root)

    # Extract all nodes using XPath queries with BPMN namespace
    # All XPath queries in NODE_TYPE_CONFIG use the "bpmn:" prefix
    # and must be executed with the namespace mapping (ns)
    nodes = _extract_all_nodes(root, ns)

    # Validate node IDs
    node_ids = _validate_node_ids(nodes)

    # Extract all sequence flow edges using BPMN namespace
    # XPath queries for BPMN elements must include the namespace mapping
    edges = []
    condition_counter = 1

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

        edges.append(BpmnEdge(
            source_id=source_id,
            target_id=target_id,
            label=label,
            condition=condition_text,
            condition_number=condition_number
        ))

    # Validate edge references
    _validate_edge_references(edges, node_ids, id_to_name)

    return BpmnDiagramModel(
        nodes=nodes,
        edges=edges,
        id_to_name=id_to_name
    )


def _create_graph():
    """Create and configure a Graphviz Digraph for BPMN rendering.

    Uses configuration from GraphConfig for consistent styling.

    Returns:
        Configured graphviz.Digraph instance
    """
    graph = graphviz.Digraph(format=GraphConfig.FORMAT)
    # Apply graph-level configuration
    graph.attr(rankdir=GraphConfig.RANKDIR, splines=GraphConfig.SPLINES)
    return graph


def _render_nodes(graph, model: BpmnDiagramModel):
    """Add all nodes from the model to the graph.

    Args:
        graph: graphviz.Digraph instance
        model: BpmnDiagramModel containing nodes to render
    """
    for node in model.nodes:
        config = NODE_TYPE_CONFIG[node.node_type]
        # Extract styling attributes (exclude xpath and default_name)
        style_attrs = {k: v for k, v in config.items()
                       if k not in ("xpath", "default_name")}
        graph.node(node.node_id, node.name, **style_attrs)


def _render_edge_with_condition(graph, edge: BpmnEdge):
    """Render an edge with a conditional expression (numbered label).

    Args:
        graph: graphviz.Digraph instance
        edge: BpmnEdge with a condition
    """
    graph.edge(
        edge.source_id,
        edge.target_id,
        label=edge.label,
        fontsize=NodeStyle.CONDITION_FONT_SIZE,
        fontcolor=NodeStyle.CONDITION_FONT_COLOR
    )


def _render_edge_with_label(graph, edge: BpmnEdge):
    """Render an edge with a name label (non-conditional).

    Args:
        graph: graphviz.Digraph instance
        edge: BpmnEdge with a label
    """
    graph.edge(
        edge.source_id,
        edge.target_id,
        label=edge.label,
        fontsize=NodeStyle.FLOW_NAME_FONT_SIZE
    )


def _render_plain_edge(graph, edge: BpmnEdge):
    """Render a plain edge without any label.

    Args:
        graph: graphviz.Digraph instance
        edge: BpmnEdge without label or condition
    """
    graph.edge(edge.source_id, edge.target_id)


def _render_edges(graph, model: BpmnDiagramModel):
    """Add all edges from the model to the graph.

    Args:
        graph: graphviz.Digraph instance
        model: BpmnDiagramModel containing edges to render
    """
    for edge in model.edges:
        if edge.condition:
            _render_edge_with_condition(graph, edge)
        elif edge.label:
            _render_edge_with_label(graph, edge)
        else:
            _render_plain_edge(graph, edge)


def render_model(model: BpmnDiagramModel, png_out: str):
    """Render a BpmnDiagramModel to a PNG file using Graphviz.

    Note: Graphviz's render() method automatically appends the format extension
    (e.g., ".png") to the output path. Therefore, if the provided path already
    includes an extension, it will be removed before rendering to avoid double
    extensions (e.g., "output.png.png").

    Args:
        model: BpmnDiagramModel to render
        png_out: Path for the output PNG file. The ".png" extension will be
            automatically handled by Graphviz, so it can be included or
            omitted.

    Raises:
        BpmnRenderError: If the output directory cannot be created or if
            Graphviz rendering fails
    """
    graph = _create_graph()
    _render_nodes(graph, model)
    _render_edges(graph, model)

    # Prepare output path (removes extension, ensures directory exists)
    output_path, _ = prepare_output_path(png_out, auto_extension=".png")

    try:
        graph.render(str(output_path), cleanup=True)
    except Exception as e:
        raise BpmnRenderError.render_failed(png_out, str(e)) from e


def render(xml_file: str, png_out: str) -> List[Condition]:
    """Render a BPMN diagram to PNG using Graphviz.

    This is a convenience function that combines model-building and rendering.
    For better testability, consider using build_model() and render_model()
    separately.

    Note: Graphviz's render() method automatically appends the format extension
    (e.g., ".png") to the output path. The path handling is done automatically.

    Args:
        xml_file: Path to the BPMN XML file
        png_out: Path for the output PNG file. The ".png" extension will be
            automatically handled by Graphviz, so it can be included or
            omitted.

    Returns:
        List of Condition objects representing conditional branches.
        Each Condition supports tuple unpacking for backward compatibility:
        number, source_name, target_name, condition = condition_obj

    Raises:
        BpmnFileError: If the XML file does not exist, is not a file,
            or cannot be read
        BpmnParseError: If the XML file is malformed or invalid
        BpmnRenderError: If the output directory cannot be created or if
            Graphviz rendering fails

    Warns:
        UserWarning: If sequence flows reference non-existent nodes or
            have missing IDs
    """
    # Build the model from XML (pure, no Graphviz dependencies)
    model = build_model(xml_file)

    # Render the model to PNG
    render_model(model, png_out)

    # Return conditions for backward compatibility
    return model.get_conditions()
