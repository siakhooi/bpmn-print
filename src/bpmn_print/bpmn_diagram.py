from typing import List, Tuple

from lxml import etree
import graphviz

from .diagram_model import BpmnDiagramModel, BpmnEdge, BpmnNode
from .node_styles import BPMN_NS, NodeStyle, NODE_TYPE_CONFIG


def _parse_bpmn_xml(xml_file):
    """Parse BPMN XML file and return root element and namespace mapping.

    Args:
        xml_file: Path to the BPMN XML file

    Returns:
        Tuple of (root_element, namespace_dict)
    """
    tree = etree.parse(xml_file)
    root = tree.getroot()
    return root, BPMN_NS


def _build_id_to_name_mapping(root):
    """Build a mapping from element IDs to their names.

    Args:
        root: Root element of the BPMN XML tree

    Returns:
        Dictionary mapping element IDs to names
    """
    id_to_name = {}
    for elem in root.findall(".//*[@id]"):
        elem_id = elem.get("id")
        elem_name = elem.get("name", elem_id)
        id_to_name[elem_id] = elem_name
    return id_to_name


def build_model(xml_file: str) -> BpmnDiagramModel:
    """Build a pure model representation of the BPMN diagram from XML.

    This function extracts all nodes and edges from the BPMN XML file
    into a model structure without any rendering dependencies. This allows
    for easy testing and potential rendering to different formats.

    Args:
        xml_file: Path to the BPMN XML file

    Returns:
        BpmnDiagramModel containing all nodes and edges
    """
    root, ns = _parse_bpmn_xml(xml_file)
    id_to_name = _build_id_to_name_mapping(root)

    # Extract all nodes
    nodes = []
    for node_type, config in NODE_TYPE_CONFIG.items():
        xpath = config["xpath"]
        default_name = config["default_name"]

        for element in root.findall(xpath, ns):
            node_id = element.get("id")
            if default_name is not None:
                name = element.get("name", default_name)
            else:
                name = element.get("name", node_id)

            nodes.append(BpmnNode(
                node_id=node_id,
                name=name,
                node_type=node_type
            ))

    # Extract all edges
    edges = []
    condition_counter = 1

    for flow in root.findall(".//bpmn:sequenceFlow", ns):
        source_id = flow.get("sourceRef")
        target_id = flow.get("targetRef")
        flow_name = flow.get("name", "")

        # Check for condition expression
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

    Args:
        model: BpmnDiagramModel to render
        png_out: Path for the output PNG file
    """
    graph = _create_graph()
    _render_nodes(graph, model)
    _render_edges(graph, model)

    # render() adds extension automatically, so remove .png from output path
    png_out_base = png_out.replace(".png", "")
    graph.render(png_out_base, cleanup=True)


def render(xml_file: str, png_out: str) -> List[Tuple[int, str, str, str]]:
    """Render a BPMN diagram to PNG using Graphviz.

    This is a convenience function that combines model-building and rendering.
    For better testability, consider using build_model() and render_model()
    separately.

    Args:
        xml_file: Path to the BPMN XML file
        png_out: Path for the output PNG file

    Returns:
        List of tuples: (number, source_name, target_name, condition)
    """
    # Build the model from XML (pure, no Graphviz dependencies)
    model = build_model(xml_file)

    # Render the model to PNG
    render_model(model, png_out)

    # Return conditions for backward compatibility
    return model.get_conditions()
