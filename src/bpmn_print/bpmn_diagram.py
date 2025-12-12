import warnings
from pathlib import Path
from typing import List, Optional, Set

from lxml import etree
from lxml.etree import XMLSyntaxError
import graphviz

from .diagram_model import (
    BpmnDiagramModel, BpmnEdge, BpmnNode, Condition
)
from .node_styles import BPMN_NS, NodeStyle, NODE_TYPE_CONFIG


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
        FileNotFoundError: If the XML file does not exist or cannot be read
        XMLSyntaxError: If the XML file is malformed or invalid
    """
    # Check if file exists before attempting to parse
    file_path = Path(xml_file)
    if not file_path.exists():
        raise FileNotFoundError(
            f"BPMN file not found: {xml_file}"
        )

    if not file_path.is_file():
        raise ValueError(
            f"Path is not a file: {xml_file}"
        )

    try:
        tree = etree.parse(xml_file)
    except OSError as e:
        raise FileNotFoundError(
            f"BPMN file cannot be read: {xml_file}"
        ) from e
    except XMLSyntaxError as e:
        raise XMLSyntaxError(
            f"Invalid XML syntax in BPMN file: {xml_file}"
        ) from e

    root = tree.getroot()
    return root, BPMN_NS


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
        return element.get("name", default_name)
    else:
        # Use node_id as fallback when element has no name attribute
        return element.get("name", node_id)


def _build_id_to_name_mapping(root):
    """Build a mapping from element IDs to their names.

    This function searches for all elements with an "id" attribute in the
    XML tree, regardless of namespace. This is intentional because:
    1. BPMN elements may have IDs
    2. Other XML elements (e.g., from extensions) may also have IDs
    3. We need to map all IDs to names for reference resolution

    Note: This XPath query (".//*[@id]") intentionally does not use the
    BPMN namespace prefix because we want to find ALL elements with IDs,
    not just BPMN elements.

    Args:
        root: Root element of the BPMN XML tree

    Returns:
        Dictionary mapping element IDs to names
    """
    # XPath without namespace: finds any element with @id attribute
    # This is intentional to capture IDs from all namespaces
    id_to_name = {}
    for elem in root.findall(".//*[@id]"):
        elem_id = elem.get("id")
        elem_name = elem.get("name", elem_id)
        id_to_name[elem_id] = elem_name
    return id_to_name


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
        FileNotFoundError: If the XML file does not exist or cannot be read
        XMLSyntaxError: If the XML file is malformed or invalid

    Warns:
        UserWarning: If sequence flows reference non-existent nodes or
            have missing IDs
    """
    root, ns = _parse_bpmn_xml(xml_file)
    id_to_name = _build_id_to_name_mapping(root)

    # Extract all nodes using XPath queries with BPMN namespace
    # All XPath queries in NODE_TYPE_CONFIG use the "bpmn:" prefix
    # and must be executed with the namespace mapping (ns)
    nodes = []
    for node_type, config in NODE_TYPE_CONFIG.items():
        # XPath with bpmn: prefix (e.g., ".//bpmn:startEvent")
        xpath = config["xpath"]
        default_name = config["default_name"]

        # XPath queries must include namespace mapping for BPMN elements
        for element in root.findall(xpath, ns):
            node_id = element.get("id")
            # Use standardized name extraction helper
            name = _get_node_name(element, default_name, node_id)

            nodes.append(BpmnNode(
                node_id=node_id,
                name=name,
                node_type=node_type
            ))

    # Validate node IDs
    node_ids = _validate_node_ids(nodes)

    # Extract all sequence flow edges using BPMN namespace
    # XPath queries for BPMN elements must include the namespace mapping
    edges = []
    condition_counter = 1

    # Find all sequenceFlow elements (BPMN namespace required)
    for flow in root.findall(".//bpmn:sequenceFlow", ns):
        source_id = flow.get("sourceRef")
        target_id = flow.get("targetRef")
        flow_name = flow.get("name", "")

        # Check for condition expression within the sequence flow
        # XPath query uses BPMN namespace
        condition_elem = flow.find(".//bpmn:conditionExpression", ns)
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

    Returns:
        Configured graphviz.Digraph instance
    """
    graph = graphviz.Digraph(format="png")
    # Left-to-right layout with polyline edges for better label support
    graph.attr(rankdir="LR", splines="polyline")
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


def _render_edges(graph, model: BpmnDiagramModel):
    """Add all edges from the model to the graph.

    Args:
        graph: graphviz.Digraph instance
        model: BpmnDiagramModel containing edges to render
    """
    for edge in model.edges:
        if edge.condition:
            # Conditional edge with numbered label
            graph.edge(
                edge.source_id,
                edge.target_id,
                label=edge.label,
                fontsize=NodeStyle.CONDITION_FONT_SIZE,
                fontcolor=NodeStyle.CONDITION_FONT_COLOR
            )
        elif edge.label:
            # Edge with name label
            graph.edge(
                edge.source_id,
                edge.target_id,
                label=edge.label,
                fontsize=NodeStyle.FLOW_NAME_FONT_SIZE
            )
        else:
            # Plain edge without label
            graph.edge(edge.source_id, edge.target_id)


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
        ValueError: If the output directory cannot be created or is invalid
        RuntimeError: If Graphviz rendering fails
    """
    graph = _create_graph()
    _render_nodes(graph, model)
    _render_edges(graph, model)

    # Graphviz render() automatically adds the format extension (e.g., ".png")
    # Remove any existing extension to avoid double extensions
    output_path = Path(png_out).with_suffix("")

    # Ensure output directory exists
    output_dir = output_path.parent
    if output_dir and not output_dir.exists():
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ValueError(
                f"Cannot create output directory: {output_dir}"
            ) from e

    try:
        graph.render(str(output_path), cleanup=True)
    except Exception as e:
        raise RuntimeError(
            f"Failed to render diagram to {png_out}: {e}"
        ) from e


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
        FileNotFoundError: If the XML file does not exist or cannot be read
        XMLSyntaxError: If the XML file is malformed or invalid
        ValueError: If the output directory cannot be created or is invalid
        RuntimeError: If Graphviz rendering fails

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
