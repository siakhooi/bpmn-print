from reportlab.platypus import (
    SimpleDocTemplate,
    Image,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
    Paragraph,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors


def make(
    pdf_path, png_file, branch_conditions, nodes, parameters,
    jexl_scripts
):
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
        Image(
            png_file,
            width=page_width,
            height=page_width * 1.2,
            kind="proportional"
        )
    )
    body.append(Spacer(1, 12))

    # Branch conditions table (if any)
    if branch_conditions:
        body.append(
            Paragraph("<b>Branch Conditions</b>", styles["Heading2"])
        )
        body.append(Spacer(1, 6))

        # Create table data
        condition_table_data = [["#", "Condition"]]
        for num, source, target, condition in branch_conditions:
            condition_table_data.append([str(num), condition])

        # Create and style table
        condition_table = Table(condition_table_data, colWidths=[30, 430])
        condition_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    # Center the # column
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ALIGN", (1, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.lightcyan),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        body.append(condition_table)
        body.append(Spacer(1, 12))

    # Nodes table (callActivity and serviceTask)
    if nodes:
        body.append(
            Paragraph(
                "<b>Nodes (Activities and Tasks)</b>",
                styles["Heading2"]
            )
        )
        body.append(Spacer(1, 6))

        # Create table data
        node_table_data = [["Node Name", "Type", "Called Element / Class"]]
        for node_name, node_type, detail in nodes:
            node_table_data.append([node_name, node_type, detail])

        # Create and style table
        node_table = Table(node_table_data, colWidths=[150, 80, 230])
        node_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.lightblue),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        body.append(node_table)
        body.append(Spacer(1, 12))

    # Parameters table
    if parameters:
        body.append(Paragraph("<b>Input Parameters</b>", styles["Heading2"]))
        body.append(Spacer(1, 6))

        # Create table data
        table_data = [["Node Name", "Parameter Name", "Value"]]
        for node_name, param_name, value, has_script in parameters:
            # Truncate long values for table display
            display_value = value if len(value) <= 50 else value[:47] + "..."
            table_data.append([node_name, param_name, display_value])

        # Create and style table
        param_table = Table(table_data, colWidths=[150, 120, 190])
        param_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        body.append(param_table)
        body.append(Spacer(1, 12))

    # JEXL scripts (full width)
    if jexl_scripts:
        body.append(Paragraph("<b>JEXL Scripts</b>", styles["Heading2"]))
        body.append(Spacer(1, 6))

        # Create custom style for script with border effect
        script_style = ParagraphStyle(
            "ScriptBox",
            parent=styles["Code"],
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
            heading = Paragraph(heading_text, styles["Heading3"])

            # Create table with background for heading
            heading_table = Table([[heading]], colWidths=[page_width])
            heading_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.lightgrey),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ]
                )
            )
            body.append(heading_table)
            body.append(Spacer(1, 3))

            # Add script content with border (can flow across pages)
            body.append(Preformatted(script, script_style))
            body.append(Spacer(1, 15))

    doc.build(body)
