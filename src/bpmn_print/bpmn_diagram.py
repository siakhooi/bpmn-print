from lxml import etree
import graphviz


def _parse_bpmn_xml(xml_file):
    """Parse BPMN XML file and return root element and namespace mapping.

    Args:
        xml_file: Path to the BPMN XML file

    Returns:
        Tuple of (root_element, namespace_dict)
    """
    tree = etree.parse(xml_file)
    root = tree.getroot()
    ns = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}
    return root, ns


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


def _add_start_events(graph, root, ns):
    """Add start event nodes to the graph.

    Args:
        graph: graphviz.Digraph instance
        root: Root element of the BPMN XML tree
        ns: Namespace dictionary
    """
    for start_event in root.findall(".//bpmn:startEvent", ns):
        node_id = start_event.get("id")
        name = start_event.get("name", "Start")
        graph.node(
            node_id,
            name,
            shape="circle",
            style="filled",
            fillcolor="lightgreen",
            width="0.6",
            height="0.6",
            fixedsize="true",
        )


def _add_end_events(graph, root, ns):
    """Add end event nodes to the graph.

    Args:
        graph: graphviz.Digraph instance
        root: Root element of the BPMN XML tree
        ns: Namespace dictionary
    """
    for end_event in root.findall(".//bpmn:endEvent", ns):
        node_id = end_event.get("id")
        name = end_event.get("name", "End")
        graph.node(
            node_id,
            name,
            shape="doublecircle",
            style="filled",
            fillcolor="lightcoral",
            width="0.6",
            height="0.6",
            fixedsize="true",
        )


def _add_tasks(graph, root, ns):
    """Add task nodes to the graph.

    Args:
        graph: graphviz.Digraph instance
        root: Root element of the BPMN XML tree
        ns: Namespace dictionary
    """
    for task in root.findall(".//bpmn:task", ns):
        node_id = task.get("id")
        name = task.get("name", node_id)
        graph.node(
            node_id,
            name,
            shape="box",
            style="rounded,filled",
            fillcolor="lightyellow",
        )


def _add_service_tasks(graph, root, ns):
    """Add service task nodes to the graph.

    Args:
        graph: graphviz.Digraph instance
        root: Root element of the BPMN XML tree
        ns: Namespace dictionary
    """
    for service_task in root.findall(".//bpmn:serviceTask", ns):
        node_id = service_task.get("id")
        name = service_task.get("name", node_id)
        graph.node(
            node_id,
            name,
            shape="box",
            style="rounded,filled",
            fillcolor="lightblue",
            penwidth="2",
        )


def _add_call_activities(graph, root, ns):
    """Add call activity nodes to the graph.

    Args:
        graph: graphviz.Digraph instance
        root: Root element of the BPMN XML tree
        ns: Namespace dictionary
    """
    for call_activity in root.findall(".//bpmn:callActivity", ns):
        node_id = call_activity.get("id")
        name = call_activity.get("name", node_id)
        graph.node(
            node_id,
            name,
            shape="box",
            style="rounded,filled,bold",
            fillcolor="wheat",
            penwidth="3",
        )


def _add_gateways(graph, root, ns):
    """Add gateway nodes (exclusive and parallel) to the graph.

    Args:
        graph: graphviz.Digraph instance
        root: Root element of the BPMN XML tree
        ns: Namespace dictionary
    """
    for gateway in root.findall(".//bpmn:exclusiveGateway", ns):
        node_id = gateway.get("id")
        name = gateway.get("name", "X")
        graph.node(
            node_id, name, shape="diamond", style="filled", fillcolor="yellow"
        )

    for gateway in root.findall(".//bpmn:parallelGateway", ns):
        node_id = gateway.get("id")
        name = gateway.get("name", "+")
        graph.node(
            node_id, name, shape="diamond", style="filled", fillcolor="orange"
        )


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
            graph.edge(sid, tid, label=label, fontsize="11", fontcolor="red")
        elif flow_name:
            graph.edge(sid, tid, label=flow_name, fontsize="10")
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
    _add_start_events(graph, root, ns)
    _add_end_events(graph, root, ns)
    _add_tasks(graph, root, ns)
    _add_service_tasks(graph, root, ns)
    _add_call_activities(graph, root, ns)
    _add_gateways(graph, root, ns)

    # Add sequence flows and collect conditions
    conditions = _add_sequence_flows(graph, root, ns, id_to_name)

    # Render to file
    _render_graph(graph, png_out)

    return conditions
