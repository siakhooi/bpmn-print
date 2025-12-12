from lxml import etree
import graphviz

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


def _create_graph():
    """Create and configure a Graphviz Digraph for BPMN rendering.

    Returns:
        Configured graphviz.Digraph instance
    """
    graph = graphviz.Digraph(format="png")
    # Left-to-right layout with polyline edges for better label support
    graph.attr(rankdir="LR", splines="polyline")
    return graph


def _add_nodes_by_type(graph, root, ns, node_type):
    """Add nodes of a specific type to the graph based on configuration.

    Args:
        graph: graphviz.Digraph instance
        root: Root element of the BPMN XML tree
        ns: Namespace dictionary
        node_type: Key from NODE_TYPE_CONFIG specifying the node type to add
    """
    config = NODE_TYPE_CONFIG[node_type]
    xpath = config["xpath"]
    default_name = config["default_name"]

    # Extract styling attributes (exclude xpath and default_name)
    style_attrs = {k: v for k, v in config.items()
                   if k not in ("xpath", "default_name")}

    for element in root.findall(xpath, ns):
        node_id = element.get("id")
        if default_name is not None:
            name = element.get("name", default_name)
        else:
            name = element.get("name", node_id)

        graph.node(node_id, name, **style_attrs)


def _add_all_nodes(graph, root, ns):
    """Add all BPMN node types to the graph.

    Args:
        graph: graphviz.Digraph instance
        root: Root element of the BPMN XML tree
        ns: Namespace dictionary
    """
    for node_type in NODE_TYPE_CONFIG.keys():
        _add_nodes_by_type(graph, root, ns, node_type)


def _add_sequence_flows(graph, root, ns, id_to_name):
    """Add sequence flow edges to the graph and collect conditions.

    Args:
        graph: graphviz.Digraph instance
        root: Root element of the BPMN XML tree
        ns: Namespace dictionary
        id_to_name: Dictionary mapping element IDs to names

    Returns:
        List of tuples: (number, source_name, target_name, condition)
    """
    conditions = []
    condition_counter = 1

    for flow in root.findall(".//bpmn:sequenceFlow", ns):
        sid = flow.get("sourceRef")
        tid = flow.get("targetRef")
        flow_name = flow.get("name", "")

        # Check for condition expression
        condition_elem = flow.find(".//bpmn:conditionExpression", ns)
        condition_text = ""
        if condition_elem is not None and condition_elem.text:
            condition_text = condition_elem.text.strip()

        # Build edge label
        if condition_text:
            # Number the conditional branch
            label = f"[{condition_counter}]"
            source_name = id_to_name.get(sid, sid)
            target_name = id_to_name.get(tid, tid)
            conditions.append(
                (condition_counter, source_name, target_name, condition_text)
            )
            condition_counter += 1
            graph.edge(
                sid,
                tid,
                label=label,
                fontsize=NodeStyle.CONDITION_FONT_SIZE,
                fontcolor=NodeStyle.CONDITION_FONT_COLOR
            )
        elif flow_name:
            graph.edge(
                sid,
                tid,
                label=flow_name,
                fontsize=NodeStyle.FLOW_NAME_FONT_SIZE)
        else:
            graph.edge(sid, tid)

    return conditions


def _render_graph(graph, png_out):
    """Render the graph to a PNG file.

    Args:
        graph: graphviz.Digraph instance
        png_out: Path for the output PNG file
    """
    # render() adds extension automatically, so remove .png from output path
    png_out_base = png_out.replace(".png", "")
    graph.render(png_out_base, cleanup=True)


def render(xml_file, png_out):
    """Render a BPMN diagram to PNG using Graphviz.

    Args:
        xml_file: Path to the BPMN XML file
        png_out: Path for the output PNG file

    Returns:
        List of tuples: (number, source_name, target_name, condition)
    """
    # Parse BPMN XML
    root, ns = _parse_bpmn_xml(xml_file)

    # Build ID to name mapping
    id_to_name = _build_id_to_name_mapping(root)

    # Create and configure graph
    graph = _create_graph()

    # Add all node types
    _add_all_nodes(graph, root, ns)

    # Add sequence flows and collect conditions
    conditions = _add_sequence_flows(graph, root, ns, id_to_name)

    # Render to file
    _render_graph(graph, png_out)

    return conditions
