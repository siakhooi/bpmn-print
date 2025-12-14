from dataclasses import dataclass
from typing import List, Tuple

from PIL import Image as PILImage
from reportlab.platypus import (
    SimpleDocTemplate,
    Image,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
    Paragraph,
    PageBreak,
    NextPageTemplate,
)
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
    StyleSheet1,
)
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.colors import Color
from reportlab.platypus.doctemplate import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
)


class PdfStyle:

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


def get_image_dimensions(image_path: str) -> Tuple[int, int]:
    """Get the width and height of a PNG image.

    Args:
        image_path: Path to the image file

    Returns:
        Tuple of (width, height) in pixels
    """
    with PILImage.open(image_path) as img:
        return img.size


def _create_standard_table_style(bg_color: Color) -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), PdfStyle.HEADER_BG_COLOR),
            ("TEXTCOLOR", (0, 0), (-1, 0), PdfStyle.HEADER_TEXT_COLOR),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), PdfStyle.HEADER_FONT_NAME),
            ("FONTSIZE", (0, 0), (-1, 0), PdfStyle.HEADER_FONT_SIZE),
            ("BOTTOMPADDING", (0, 0), (-1, 0), PdfStyle.HEADER_BOTTOM_PADDING),
            ("BACKGROUND", (0, 1), (-1, -1), bg_color),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                PdfStyle.GRID_LINE_WIDTH,
                PdfStyle.GRID_COLOR,
            ),
            ("FONTSIZE", (0, 1), (-1, -1), PdfStyle.BODY_FONT_SIZE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
    )


def _create_condition_table(conditions: List) -> Table:

    # Create table data
    table_data = [["#", "Condition"]]
    for cond in conditions:
        table_data.append([str(cond.num), cond.expression])

    # Create and style table
    table = Table(
        table_data,
        colWidths=[PdfStyle.CONDITION_COL_NUMBER, PdfStyle.CONDITION_COL_TEXT],
    )

    # Apply standard style with custom alignment for # column
    style = _create_standard_table_style(PdfStyle.CONDITION_BG_COLOR)
    style.add("ALIGN", (0, 0), (0, -1), "CENTER")  # Center # column
    table.setStyle(style)

    return table


def _create_node_table(nodes: List) -> Table:

    # Create table data
    table_data = [["Node Name", "Type", "Called Element / Class"]]
    for node in nodes:
        table_data.append([node.name, node.type, node.target])

    # Create and style table
    table = Table(
        table_data,
        colWidths=[
            PdfStyle.NODE_COL_NAME,
            PdfStyle.NODE_COL_TYPE,
            PdfStyle.NODE_COL_DETAIL,
        ],
    )
    table.setStyle(_create_standard_table_style(PdfStyle.NODE_BG_COLOR))

    return table


def _create_parameter_table(parameters: List) -> Table:

    # Create table data
    table_data = [["Node Name", "Parameter Name", "Value"]]
    for param in parameters:
        # Note: param.has_script could be used in the future to apply different
        # styling to parameters with associated JEXL scripts

        # Truncate long values for table display
        max_len = PdfStyle.MAX_VALUE_LENGTH
        if len(param.value) <= max_len:
            display_value = param.value
        else:
            suffix_len = PdfStyle.TRUNCATE_SUFFIX_LENGTH
            display_value = param.value[: max_len - suffix_len] + "..."
        table_data.append([param.node_name, param.param_name, display_value])

    # Create and style table
    table = Table(
        table_data,
        colWidths=[
            PdfStyle.PARAM_COL_NODE,
            PdfStyle.PARAM_COL_NAME,
            PdfStyle.PARAM_COL_VALUE,
        ],
    )
    table.setStyle(_create_standard_table_style(PdfStyle.PARAM_BG_COLOR))

    return table


def _create_script_section(
    scripts: List, styles: StyleSheet1, page_width: float
) -> List:
    """Create flowables for JEXL script section.

    Args:
        scripts: List of Script objects
        styles: ReportLab sample stylesheet
        page_width: Width of the page for sizing

    Returns:
        List of flowable elements (headings, spacers, preformatted text)
    """
    flowables = []

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

    for _, script in enumerate(scripts, 1):
        # Create heading with background
        heading_text = f"<b>{script.node_name}</b> | {script.param_name}"
        heading = Paragraph(heading_text, styles["Heading3"])

        # Create table with background for heading
        heading_table = Table([[heading]], colWidths=[page_width])
        heading_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, -1),
                        PdfStyle.SCRIPT_HEADING_BG_COLOR,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        PdfStyle.SCRIPT_HEADING_TOP_PADDING,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        PdfStyle.SCRIPT_HEADING_BOTTOM_PADDING,
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        PdfStyle.SCRIPT_HEADING_LEFT_PADDING,
                    ),
                ]
            )
        )
        flowables.append(heading_table)
        flowables.append(Spacer(1, PdfStyle.SPACER_SMALL))

        # Add script content with border (can flow across pages)
        flowables.append(Preformatted(script.text, script_style))
        flowables.append(Spacer(1, PdfStyle.SPACER_XLARGE))

    return flowables


def _create_document(
    pdf_path: str, use_landscape: bool
) -> BaseDocTemplate | SimpleDocTemplate:
    """Create PDF document with appropriate page templates.

    Args:
        pdf_path: Path where the PDF file will be saved
        use_landscape: Whether to use mixed landscape/portrait layout

    Returns:
        Configured document template
    """
    if use_landscape:
        doc = BaseDocTemplate(pdf_path)

        # Define landscape template for diagram
        landscape_frame = Frame(
            PdfStyle.MARGIN_LEFT,
            PdfStyle.MARGIN_BOTTOM,
            landscape(A4)[0] - PdfStyle.MARGIN_LEFT - PdfStyle.MARGIN_RIGHT,
            landscape(A4)[1] - PdfStyle.MARGIN_TOP - PdfStyle.MARGIN_BOTTOM,
            id="landscape_frame",
        )
        landscape_template = PageTemplate(
            id="Landscape",
            frames=[landscape_frame],
            pagesize=landscape(A4),
        )

        # Define portrait template for content
        portrait_frame = Frame(
            PdfStyle.MARGIN_LEFT,
            PdfStyle.MARGIN_BOTTOM,
            A4[0] - PdfStyle.MARGIN_LEFT - PdfStyle.MARGIN_RIGHT,
            A4[1] - PdfStyle.MARGIN_TOP - PdfStyle.MARGIN_BOTTOM,
            id="portrait_frame",
        )
        portrait_template = PageTemplate(
            id="Portrait", frames=[portrait_frame], pagesize=A4
        )

        doc.addPageTemplates([landscape_template, portrait_template])
    else:
        # Standard portrait layout
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            leftMargin=PdfStyle.MARGIN_LEFT,
            rightMargin=PdfStyle.MARGIN_RIGHT,
            topMargin=PdfStyle.MARGIN_TOP,
            bottomMargin=PdfStyle.MARGIN_BOTTOM,
        )

    return doc


def _get_page_width(use_landscape: bool) -> float:
    """Calculate usable page width for content.

    Args:
        use_landscape: Whether using landscape orientation

    Returns:
        Page width in points
    """
    if use_landscape:
        return landscape(A4)[0] - PdfStyle.MARGIN_LEFT - PdfStyle.MARGIN_RIGHT
    return A4[0] - PdfStyle.MARGIN_LEFT - PdfStyle.MARGIN_RIGHT


def _build_body(
    data: PdfData,
    styles: StyleSheet1,
    use_landscape: bool,
    initial_page_width: float,
) -> List:
    """Build the document body with all sections.

    Args:
        data: PdfData container with all BPMN information
        styles: ReportLab sample stylesheet
        use_landscape: Whether diagram is on landscape page
        initial_page_width: Page width for diagram

    Returns:
        List of flowable elements
    """
    body = []

    # Diagram
    body.append(
        Image(
            data.png_file,
            width=initial_page_width,
            height=initial_page_width * PdfStyle.DIAGRAM_HEIGHT_RATIO,
            kind="proportional",
        )
    )

    # Switch to portrait for content if using landscape
    if use_landscape:
        body.append(NextPageTemplate("Portrait"))
        body.append(PageBreak())
        page_width = _get_page_width(False)  # Portrait width
    else:
        page_width = initial_page_width

    body.append(Spacer(1, PdfStyle.SPACER_LARGE))

    # Branch conditions table
    if data.branch_conditions:
        body.append(Paragraph("<b>Branch Conditions</b>", styles["Heading2"]))
        body.append(Spacer(1, PdfStyle.SPACER_MEDIUM))
        body.append(_create_condition_table(data.branch_conditions))
        body.append(Spacer(1, PdfStyle.SPACER_LARGE))

    # Nodes table
    if data.nodes:
        body.append(
            Paragraph(
                "<b>Nodes (Activities and Tasks)</b>", styles["Heading2"]
            )
        )
        body.append(Spacer(1, PdfStyle.SPACER_MEDIUM))
        body.append(_create_node_table(data.nodes))
        body.append(Spacer(1, PdfStyle.SPACER_LARGE))

    # Parameters table
    if data.parameters:
        body.append(Paragraph("<b>Input Parameters</b>", styles["Heading2"]))
        body.append(Spacer(1, PdfStyle.SPACER_MEDIUM))
        body.append(_create_parameter_table(data.parameters))
        body.append(Spacer(1, PdfStyle.SPACER_LARGE))

    # JEXL scripts
    if data.jexl_scripts:
        body.append(Paragraph("<b>JEXL Scripts</b>", styles["Heading2"]))
        body.append(Spacer(1, PdfStyle.SPACER_MEDIUM))
        body.extend(
            _create_script_section(data.jexl_scripts, styles, page_width)
        )

    return body


def make(
    pdf_path: str, data: PdfData, landscape_threshold: int = 2200
) -> None:
    """Generate a PDF document from BPMN data.

    Args:
        pdf_path: Path where the PDF file will be saved
        data: PdfData container with all BPMN information to render
        landscape_threshold: Width in pixels above which diagram
            gets landscape page
    """
    # Determine layout based on diagram width
    img_width, _ = get_image_dimensions(data.png_file)
    use_landscape = img_width > landscape_threshold

    # Create document with appropriate page templates
    doc = _create_document(pdf_path, use_landscape)

    # Build document body
    styles = getSampleStyleSheet()
    page_width = _get_page_width(use_landscape)
    body = _build_body(data, styles, use_landscape, page_width)

    doc.build(body)
