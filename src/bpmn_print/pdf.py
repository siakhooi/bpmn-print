from dataclasses import dataclass
from typing import List

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


class PdfStyle:
    """Styling constants for PDF generation.

    This class centralizes all styling values used in PDF generation,
    making them easy to customize without modifying the rendering code.
    """
    # Document margins
    MARGIN_LEFT = 10 * mm
    MARGIN_RIGHT = 10 * mm
    MARGIN_TOP = 10 * mm
    MARGIN_BOTTOM = 10 * mm

    # Diagram sizing
    DIAGRAM_HEIGHT_RATIO = 1.2

    # Spacing
    SPACER_LARGE = 12
    SPACER_MEDIUM = 6
    SPACER_SMALL = 3
    SPACER_XLARGE = 15

    # Table column widths
    CONDITION_COL_NUMBER = 30
    CONDITION_COL_TEXT = 430

    NODE_COL_NAME = 150
    NODE_COL_TYPE = 80
    NODE_COL_DETAIL = 230

    PARAM_COL_NODE = 150
    PARAM_COL_NAME = 120
    PARAM_COL_VALUE = 190

    # Value truncation
    MAX_VALUE_LENGTH = 50
    TRUNCATE_SUFFIX_LENGTH = 3  # "..."

    # Table header styling
    HEADER_BG_COLOR = colors.grey
    HEADER_TEXT_COLOR = colors.whitesmoke
    HEADER_FONT_NAME = "Helvetica-Bold"
    HEADER_FONT_SIZE = 10
    HEADER_BOTTOM_PADDING = 12

    # Table body styling
    BODY_FONT_SIZE = 8
    GRID_LINE_WIDTH = 1
    GRID_COLOR = colors.black

    # Table background colors
    CONDITION_BG_COLOR = colors.lightcyan
    NODE_BG_COLOR = colors.lightblue
    PARAM_BG_COLOR = colors.beige
    SCRIPT_HEADING_BG_COLOR = colors.lightgrey

    # Script box styling
    SCRIPT_LEFT_INDENT = 10
    SCRIPT_RIGHT_INDENT = 10
    SCRIPT_SPACE_BEFORE = 6
    SCRIPT_SPACE_AFTER = 6
    SCRIPT_BORDER_WIDTH = 2
    SCRIPT_BORDER_COLOR = colors.grey
    SCRIPT_BORDER_PADDING = 8
    SCRIPT_BACK_COLOR = colors.white

    # Script heading table padding
    SCRIPT_HEADING_TOP_PADDING = 6
    SCRIPT_HEADING_BOTTOM_PADDING = 6
    SCRIPT_HEADING_LEFT_PADDING = 10


@dataclass
class PdfData:
    """Container for BPMN data to be rendered in PDF.

    Groups all the extracted BPMN information needed for PDF generation,
    reducing the number of parameters passed to the make() function.

    Attributes:
        png_file: Path to the diagram image file
        branch_conditions: List of conditional branches
        nodes: List of BPMN nodes (activities and tasks)
        parameters: List of input parameters
        jexl_scripts: List of JEXL scripts
    """
    png_file: str
    branch_conditions: List
    nodes: List
    parameters: List
    jexl_scripts: List


def make(pdf_path: str, data: PdfData) -> None:
    """Generate a PDF document from BPMN data.

    Args:
        pdf_path: Path where the PDF file will be saved
        data: PdfData container with all BPMN information to render
    """
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=PdfStyle.MARGIN_LEFT,
        rightMargin=PdfStyle.MARGIN_RIGHT,
        topMargin=PdfStyle.MARGIN_TOP,
        bottomMargin=PdfStyle.MARGIN_BOTTOM,
    )

    styles = getSampleStyleSheet()
    body = []

    # Diagram (fit to page width, limit height to avoid overflow)
    page_width = A4[0] - PdfStyle.MARGIN_LEFT - PdfStyle.MARGIN_RIGHT
    body.append(
        Image(
            data.png_file,
            width=page_width,
            height=page_width * PdfStyle.DIAGRAM_HEIGHT_RATIO,
            kind="proportional"
        )
    )
    body.append(Spacer(1, PdfStyle.SPACER_LARGE))

    # Branch conditions table (if any)
    if data.branch_conditions:
        body.append(
            Paragraph("<b>Branch Conditions</b>", styles["Heading2"])
        )
        body.append(Spacer(1, PdfStyle.SPACER_MEDIUM))

        # Create table data
        condition_table_data = [["#", "Condition"]]
        for num, source, target, condition in data.branch_conditions:
            condition_table_data.append([str(num), condition])

        # Create and style table
        condition_table = Table(
            condition_table_data,
            colWidths=[PdfStyle.CONDITION_COL_NUMBER,
                       PdfStyle.CONDITION_COL_TEXT]
        )
        condition_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0),
                     PdfStyle.HEADER_BG_COLOR),
                    ("TEXTCOLOR", (0, 0), (-1, 0),
                     PdfStyle.HEADER_TEXT_COLOR),
                    # Center the # column
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ALIGN", (1, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0),
                     PdfStyle.HEADER_FONT_NAME),
                    ("FONTSIZE", (0, 0), (-1, 0),
                     PdfStyle.HEADER_FONT_SIZE),
                    ("BOTTOMPADDING", (0, 0), (-1, 0),
                     PdfStyle.HEADER_BOTTOM_PADDING),
                    ("BACKGROUND", (0, 1), (-1, -1),
                     PdfStyle.CONDITION_BG_COLOR),
                    ("GRID", (0, 0), (-1, -1),
                     PdfStyle.GRID_LINE_WIDTH, PdfStyle.GRID_COLOR),
                    ("FONTSIZE", (0, 1), (-1, -1),
                     PdfStyle.BODY_FONT_SIZE),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        body.append(condition_table)
        body.append(Spacer(1, PdfStyle.SPACER_LARGE))

    # Nodes table (callActivity and serviceTask)
    if data.nodes:
        body.append(
            Paragraph(
                "<b>Nodes (Activities and Tasks)</b>",
                styles["Heading2"]
            )
        )
        body.append(Spacer(1, PdfStyle.SPACER_MEDIUM))

        # Create table data
        node_table_data = [["Node Name", "Type", "Called Element / Class"]]
        for node_name, node_type, detail in data.nodes:
            node_table_data.append([node_name, node_type, detail])

        # Create and style table
        node_table = Table(
            node_table_data,
            colWidths=[PdfStyle.NODE_COL_NAME, PdfStyle.NODE_COL_TYPE,
                       PdfStyle.NODE_COL_DETAIL]
        )
        node_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0),
                     PdfStyle.HEADER_BG_COLOR),
                    ("TEXTCOLOR", (0, 0), (-1, 0),
                     PdfStyle.HEADER_TEXT_COLOR),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0),
                     PdfStyle.HEADER_FONT_NAME),
                    ("FONTSIZE", (0, 0), (-1, 0),
                     PdfStyle.HEADER_FONT_SIZE),
                    ("BOTTOMPADDING", (0, 0), (-1, 0),
                     PdfStyle.HEADER_BOTTOM_PADDING),
                    ("BACKGROUND", (0, 1), (-1, -1),
                     PdfStyle.NODE_BG_COLOR),
                    ("GRID", (0, 0), (-1, -1),
                     PdfStyle.GRID_LINE_WIDTH, PdfStyle.GRID_COLOR),
                    ("FONTSIZE", (0, 1), (-1, -1),
                     PdfStyle.BODY_FONT_SIZE),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        body.append(node_table)
        body.append(Spacer(1, PdfStyle.SPACER_LARGE))

    # Parameters table
    if data.parameters:
        body.append(Paragraph("<b>Input Parameters</b>", styles["Heading2"]))
        body.append(Spacer(1, PdfStyle.SPACER_MEDIUM))

        # Create table data
        table_data = [["Node Name", "Parameter Name", "Value"]]
        for node_name, param_name, value, has_script in data.parameters:
            # Truncate long values for table display
            max_len = PdfStyle.MAX_VALUE_LENGTH
            if len(value) <= max_len:
                display_value = value
            else:
                suffix_len = PdfStyle.TRUNCATE_SUFFIX_LENGTH
                display_value = value[:max_len - suffix_len] + "..."
            table_data.append([node_name, param_name, display_value])

        # Create and style table
        param_table = Table(
            table_data,
            colWidths=[PdfStyle.PARAM_COL_NODE, PdfStyle.PARAM_COL_NAME,
                       PdfStyle.PARAM_COL_VALUE]
        )
        param_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0),
                     PdfStyle.HEADER_BG_COLOR),
                    ("TEXTCOLOR", (0, 0), (-1, 0),
                     PdfStyle.HEADER_TEXT_COLOR),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0),
                     PdfStyle.HEADER_FONT_NAME),
                    ("FONTSIZE", (0, 0), (-1, 0),
                     PdfStyle.HEADER_FONT_SIZE),
                    ("BOTTOMPADDING", (0, 0), (-1, 0),
                     PdfStyle.HEADER_BOTTOM_PADDING),
                    ("BACKGROUND", (0, 1), (-1, -1),
                     PdfStyle.PARAM_BG_COLOR),
                    ("GRID", (0, 0), (-1, -1),
                     PdfStyle.GRID_LINE_WIDTH, PdfStyle.GRID_COLOR),
                    ("FONTSIZE", (0, 1), (-1, -1),
                     PdfStyle.BODY_FONT_SIZE),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        body.append(param_table)
        body.append(Spacer(1, PdfStyle.SPACER_LARGE))

    # JEXL scripts (full width)
    if data.jexl_scripts:
        body.append(Paragraph("<b>JEXL Scripts</b>", styles["Heading2"]))
        body.append(Spacer(1, PdfStyle.SPACER_MEDIUM))

        # Create custom style for script with border effect
        script_style = ParagraphStyle(
            "ScriptBox",
            parent=styles["Code"],
            leftIndent=PdfStyle.SCRIPT_LEFT_INDENT,
            rightIndent=PdfStyle.SCRIPT_RIGHT_INDENT,
            spaceBefore=PdfStyle.SCRIPT_SPACE_BEFORE,
            spaceAfter=PdfStyle.SCRIPT_SPACE_AFTER,
            borderWidth=PdfStyle.SCRIPT_BORDER_WIDTH,
            borderColor=PdfStyle.SCRIPT_BORDER_COLOR,
            borderPadding=PdfStyle.SCRIPT_BORDER_PADDING,
            backColor=PdfStyle.SCRIPT_BACK_COLOR,
        )

        for idx, (script, node_name, param_name) in enumerate(
            data.jexl_scripts, 1
        ):
            # Create heading with background
            heading_text = f"<b>{node_name}</b> | {param_name}"
            heading = Paragraph(heading_text, styles["Heading3"])

            # Create table with background for heading
            heading_table = Table([[heading]], colWidths=[page_width])
            heading_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1),
                         PdfStyle.SCRIPT_HEADING_BG_COLOR),
                        ("TOPPADDING", (0, 0), (-1, -1),
                         PdfStyle.SCRIPT_HEADING_TOP_PADDING),
                        ("BOTTOMPADDING", (0, 0), (-1, -1),
                         PdfStyle.SCRIPT_HEADING_BOTTOM_PADDING),
                        ("LEFTPADDING", (0, 0), (-1, -1),
                         PdfStyle.SCRIPT_HEADING_LEFT_PADDING),
                    ]
                )
            )
            body.append(heading_table)
            body.append(Spacer(1, PdfStyle.SPACER_SMALL))

            # Add script content with border (can flow across pages)
            body.append(Preformatted(script, script_style))
            body.append(Spacer(1, PdfStyle.SPACER_XLARGE))

    doc.build(body)
