from lxml import etree
import graphviz


def render(xml_file, png_out):
    """Render a BPMN diagram to PNG using Graphviz.
    Args:
        xml_file: Path to the BPMN XML file
        png_out: Path for the output PNG file
    Returns:
        List of tuples: (number, source_name, target_name, condition)
    """
    # Load BPMN using graphviz with better styling
    graph = graphviz.Digraph(format="png")
    # Left-to-right layout with polyline edges for better label support
    graph.attr(rankdir="LR", splines="polyline")

    tree = etree.parse(xml_file)
    root = tree.getroot()
    ns = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}

    # Track conditions for table display
    # List of tuples: (number, source_name, target_name, condition)
    conditions = []
    condition_counter = 1

    # Create ID to name mapping for all nodes
    id_to_name = {}
    for elem in root.findall(".//*[@id]"):
        elem_id = elem.get("id")
        elem_name = elem.get("name", elem_id)
        id_to_name[elem_id] = elem_name

    # Start events - circle
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

    # End events - double circle
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

    # Tasks - box
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

    # Service Tasks - box with bold border
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

    # Call Activities - box with thick border
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

    # Gateways - diamond
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

    # Sequence flows with arrows and conditions
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

    # render() adds extension automatically, so remove .png from output path
    png_out_base = png_out.replace(".png", "")
    graph.render(png_out_base, cleanup=True)

    return conditions
