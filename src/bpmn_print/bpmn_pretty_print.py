import os
from lxml import etree
from reportlab.platypus import (
    SimpleDocTemplate, Image, Preformatted, Spacer, Table, TableStyle,
    Paragraph
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
import graphviz


def render_bpmn_diagram(xml_file, png_out):
    # Load BPMN using graphviz with better styling
    graph = graphviz.Digraph(format='png')
    # Left-to-right layout with polyline edges for better label support
    graph.attr(rankdir='LR', splines='polyline')

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
            node_id, name, shape='circle', style='filled',
            fillcolor='lightgreen', width='0.6', height='0.6',
            fixedsize='true'
        )

    # End events - double circle
    for end_event in root.findall(".//bpmn:endEvent", ns):
        node_id = end_event.get("id")
        name = end_event.get("name", "End")
        graph.node(
            node_id, name, shape='doublecircle', style='filled',
            fillcolor='lightcoral', width='0.6', height='0.6',
            fixedsize='true'
        )

    # Tasks - box
    for task in root.findall(".//bpmn:task", ns):
        node_id = task.get("id")
        name = task.get("name", node_id)
        graph.node(
            node_id, name, shape='box', style='rounded,filled',
            fillcolor='lightyellow'
        )

    # Service Tasks - box with bold border
    for service_task in root.findall(".//bpmn:serviceTask", ns):
        node_id = service_task.get("id")
        name = service_task.get("name", node_id)
        graph.node(
            node_id, name, shape='box', style='rounded,filled',
            fillcolor='lightblue', penwidth='2'
        )

    # Call Activities - box with thick border
    for call_activity in root.findall(".//bpmn:callActivity", ns):
        node_id = call_activity.get("id")
        name = call_activity.get("name", node_id)
        graph.node(
            node_id, name, shape='box', style='rounded,filled,bold',
            fillcolor='wheat', penwidth='3'
        )

    # Gateways - diamond
    for gateway in root.findall(".//bpmn:exclusiveGateway", ns):
        node_id = gateway.get("id")
        name = gateway.get("name", "X")
        graph.node(
            node_id, name, shape='diamond', style='filled',
            fillcolor='yellow'
        )

    for gateway in root.findall(".//bpmn:parallelGateway", ns):
        node_id = gateway.get("id")
        name = gateway.get("name", "+")
        graph.node(
            node_id, name, shape='diamond', style='filled',
            fillcolor='orange'
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
            graph.edge(
                sid, tid, label=label, fontsize='11', fontcolor='red'
            )
        elif flow_name:
            graph.edge(sid, tid, label=flow_name, fontsize='10')
        else:
            graph.edge(sid, tid)

    # render() adds extension automatically, so remove .png from output path
    png_out_base = png_out.replace('.png', '')
    graph.render(png_out_base, cleanup=True)

    return conditions


def extract_data(xml_file):
    tree = etree.parse(xml_file)
    root = tree.getroot()
    ns = {
        "camunda": "http://camunda.org/schema/1.0/bpmn",
        "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"
    }

    def find_parent_with_id(element):
        """Traverse up the tree to find the first ancestor with an
        'id' attribute
        """
        current = element
        while current is not None:
            if 'id' in current.attrib:
                return current.get('id')
            current = current.getparent()
        return 'unknown'

    # Create ID to name mapping for all elements
    id_to_name = {}
    for elem in root.findall(".//*[@id]"):
        elem_id = elem.get('id')
        elem_name = elem.get('name', elem_id)
        id_to_name[elem_id] = elem_name

    # Collect node information (callActivity and serviceTask)
    # List of tuples: (node_name, node_type, called_element_or_class)
    nodes = []

    # Find all callActivity elements
    for call_activity in root.findall(".//bpmn:callActivity", ns):
        node_name = call_activity.get(
            'name', call_activity.get('id', 'unknown')
        )
        called_element = call_activity.get('calledElement', '')
        nodes.append((node_name, 'callActivity', called_element))

    # Find all serviceTask elements
    for service_task in root.findall(".//bpmn:serviceTask", ns):
        node_name = service_task.get(
            'name', service_task.get('id', 'unknown')
        )
        class_name = service_task.get(
            '{http://camunda.org/schema/1.0/bpmn}class', ''
        )
        # Simplify class name - show only the last part
        simple_class = class_name.split('.')[-1] if class_name else ''
        nodes.append((node_name, 'serviceTask', simple_class))

    # List of tuples: (node_name, param_name, value, has_script)
    parameters = []
    # List of tuples: (script_text, node_name, parameter_name)
    scripts = []

    # All script elements
    for scr in root.findall(".//camunda:script", ns):
        node_id = find_parent_with_id(scr)
        node_name = id_to_name.get(node_id, node_id)
        param_name = scr.getparent().get('name', 'script')
        scripts.append((scr.text or "", node_name, param_name))

    # inputOutput mappings - collect all inputParameters
    for inp in root.findall(".//camunda:inputParameter", ns):
        node_id = find_parent_with_id(inp)
        node_name = id_to_name.get(node_id, node_id)
        param_name = inp.get('name', 'inputParameter')

        # Check if it contains a script element
        script_elem = inp.find(".//camunda:script", ns)
        if script_elem is not None:
            # Has script - will be shown in scripts section
            parameters.append(
                (node_name, param_name, '[See JEXL Scripts]', True)
            )
        elif inp.text:
            # Has text content
            if "#{ " in inp.text or "${ " in inp.text:
                # JEXL expression - add to scripts
                scripts.append((inp.text, node_name, param_name))
                parameters.append(
                    (node_name, param_name, '[See JEXL Scripts]', True)
                )
            else:
                # Simple value
                parameters.append((node_name, param_name, inp.text, False))
        else:
            # Empty or other
            parameters.append((node_name, param_name, '', False))

    return nodes, parameters, scripts


def make_pdf(bpmn_file, pdf_path):
    # 1. Render diagram to PNG
    png_file = pdf_path.replace(".pdf", ".png")
    branch_conditions = render_bpmn_diagram(bpmn_file, png_file)

    # 2. Extract data
    nodes, parameters, jexl_scripts = extract_data(bpmn_file)

    # 3. Prepare PDF
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )

    styles = getSampleStyleSheet()
    body = []

    # Diagram (fit to page width, limit height to avoid overflow)
    page_width = A4[0] - 20 * mm  # A4 width minus margins
    body.append(
        Image(png_file, width=page_width, height=page_width * 1.2,
              kind='proportional')
    )
    body.append(Spacer(1, 12))

    # Branch conditions table (if any)
    if branch_conditions:
        body.append(Paragraph("<b>Branch Conditions</b>", styles['Heading2']))
        body.append(Spacer(1, 6))

        # Create table data
        condition_table_data = [['#', 'Condition']]
        for num, source, target, condition in branch_conditions:
            condition_table_data.append([str(num), condition])

        # Create and style table
        condition_table = Table(condition_table_data, colWidths=[30, 430])
        condition_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Center the # column
            ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightcyan),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        body.append(condition_table)
        body.append(Spacer(1, 12))

    # Nodes table (callActivity and serviceTask)
    if nodes:
        body.append(
            Paragraph("<b>Nodes (Activities and Tasks)</b>",
                      styles['Heading2'])
        )
        body.append(Spacer(1, 6))

        # Create table data
        node_table_data = [['Node Name', 'Type', 'Called Element / Class']]
        for node_name, node_type, detail in nodes:
            node_table_data.append([node_name, node_type, detail])

        # Create and style table
        node_table = Table(node_table_data, colWidths=[150, 80, 230])
        node_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        body.append(node_table)
        body.append(Spacer(1, 12))

    # Parameters table
    if parameters:
        body.append(Paragraph("<b>Input Parameters</b>", styles['Heading2']))
        body.append(Spacer(1, 6))

        # Create table data
        table_data = [['Node Name', 'Parameter Name', 'Value']]
        for node_name, param_name, value, has_script in parameters:
            # Truncate long values for table display
            display_value = value if len(value) <= 50 else value[:47] + '...'
            table_data.append([node_name, param_name, display_value])

        # Create and style table
        param_table = Table(table_data, colWidths=[150, 120, 190])
        param_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        body.append(param_table)
        body.append(Spacer(1, 12))

    # JEXL scripts (full width)
    if jexl_scripts:
        body.append(Paragraph("<b>JEXL Scripts</b>", styles['Heading2']))
        body.append(Spacer(1, 6))

        from reportlab.lib.styles import ParagraphStyle

        # Create custom style for script with border effect
        script_style = ParagraphStyle(
            'ScriptBox',
            parent=styles['Code'],
            leftIndent=10,
            rightIndent=10,
            spaceBefore=6,
            spaceAfter=6,
            borderWidth=2,
            borderColor=colors.grey,
            borderPadding=8,
            backColor=colors.white,
        )

        for idx, (script, node_name, param_name) in enumerate(jexl_scripts, 1):
            # Create heading with background
            heading_text = f"<b>{node_name}</b> | {param_name}"
            heading = Paragraph(heading_text, styles['Heading3'])

            # Create table with background for heading
            heading_table = Table([[heading]], colWidths=[page_width])
            heading_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ]))
            body.append(heading_table)
            body.append(Spacer(1, 3))

            # Add script content with border (can flow across pages)
            body.append(Preformatted(script, script_style))
            body.append(Spacer(1, 15))

    doc.build(body)


def pretty_print(input_folder: str, output_folder: str) -> None:
    os.makedirs(output_folder, exist_ok=True)

    for file in os.listdir(input_folder):
        if file.endswith(".bpmn"):
            src = os.path.join(input_folder, file)
            dest = os.path.join(output_folder, file.replace(".bpmn", ".pdf"))
            make_pdf(src, dest)
    print("Done.")
