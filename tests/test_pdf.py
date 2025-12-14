import os
import tempfile
from unittest.mock import Mock, patch, MagicMock

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle

from bpmn_print.pdf import (
    PdfStyle,
    PdfData,
    _create_standard_table_style,
    _create_condition_table,
    _create_node_table,
    _create_parameter_table,
    _create_script_section,
    make,
)


class TestPdfStyle:
    """Tests for PdfStyle class constants."""

    def test_margin_constants(self):
        """Test document margin constants are defined."""
        assert PdfStyle.MARGIN_LEFT > 0
        assert PdfStyle.MARGIN_RIGHT > 0
        assert PdfStyle.MARGIN_TOP > 0
        assert PdfStyle.MARGIN_BOTTOM > 0

    def test_spacing_constants(self):
        """Test spacing constants are defined."""
        assert PdfStyle.SPACER_LARGE == 12
        assert PdfStyle.SPACER_MEDIUM == 6
        assert PdfStyle.SPACER_SMALL == 3
        assert PdfStyle.SPACER_XLARGE == 15

    def test_column_width_constants(self):
        """Test table column width constants."""
        assert PdfStyle.CONDITION_COL_NUMBER == 30
        assert PdfStyle.CONDITION_COL_TEXT == 430
        assert PdfStyle.NODE_COL_NAME == 150
        assert PdfStyle.NODE_COL_TYPE == 80
        assert PdfStyle.NODE_COL_DETAIL == 230
        assert PdfStyle.PARAM_COL_NODE == 150
        assert PdfStyle.PARAM_COL_NAME == 120
        assert PdfStyle.PARAM_COL_VALUE == 190

    def test_value_truncation_constants(self):
        """Test value truncation constants."""
        assert PdfStyle.MAX_VALUE_LENGTH == 50
        assert PdfStyle.TRUNCATE_SUFFIX_LENGTH == 3

    def test_header_styling_constants(self):
        """Test table header styling constants."""
        assert PdfStyle.HEADER_BG_COLOR == colors.grey
        assert PdfStyle.HEADER_TEXT_COLOR == colors.whitesmoke
        assert PdfStyle.HEADER_FONT_NAME == "Helvetica-Bold"
        assert PdfStyle.HEADER_FONT_SIZE == 10
        assert PdfStyle.HEADER_BOTTOM_PADDING == 12

    def test_background_color_constants(self):
        """Test table background color constants."""
        assert PdfStyle.CONDITION_BG_COLOR == colors.lightcyan
        assert PdfStyle.NODE_BG_COLOR == colors.lightblue
        assert PdfStyle.PARAM_BG_COLOR == colors.beige
        assert PdfStyle.SCRIPT_HEADING_BG_COLOR == colors.lightgrey


class TestPdfData:
    """Tests for PdfData dataclass."""

    def test_pdf_data_creation(self):
        """Test creating a PdfData instance."""
        data = PdfData(
            png_file="diagram.png",
            branch_conditions=[],
            nodes=[],
            parameters=[],
            jexl_scripts=[],
        )

        assert data.png_file == "diagram.png"
        assert data.branch_conditions == []
        assert data.nodes == []
        assert data.parameters == []
        assert data.jexl_scripts == []

    def test_pdf_data_with_content(self):
        """Test PdfData with actual content."""
        conditions = [Mock(num=1, expression="x > 0")]
        nodes = [Mock(name="Task1", type="serviceTask", target="MyClass")]
        parameters = [
            Mock(
                node_name="Task1",
                param_name="p1",
                value="v1",
                has_script=False,
            )
        ]
        scripts = [Mock(node_name="Task1", param_name="s1", text="code")]

        data = PdfData(
            png_file="test.png",
            branch_conditions=conditions,
            nodes=nodes,
            parameters=parameters,
            jexl_scripts=scripts,
        )

        assert len(data.branch_conditions) == 1
        assert len(data.nodes) == 1
        assert len(data.parameters) == 1
        assert len(data.jexl_scripts) == 1


class TestCreateStandardTableStyle:
    """Tests for _create_standard_table_style function."""

    def test_returns_table_style(self):
        """Test that function returns a TableStyle instance."""
        style = _create_standard_table_style(colors.lightblue)

        assert isinstance(style, TableStyle)

    def test_applies_background_color(self):
        """Test that custom background color is applied."""
        bg_color = colors.lightgreen
        style = _create_standard_table_style(bg_color)

        # Check that the background color command is in the style
        commands = style.getCommands()
        # Find background command for body rows (starting at row 1)
        bg_commands = [
            cmd
            for cmd in commands
            if cmd[0] == "BACKGROUND" and cmd[1][1] == 1  # row 1 start
        ]

        assert len(bg_commands) > 0
        # The color is the last element in the command tuple
        assert bg_commands[0][-1] == bg_color

    def test_includes_header_styling(self):
        """Test that header styling commands are included."""
        style = _create_standard_table_style(colors.white)
        commands = style.getCommands()

        # Check for header background
        header_bg = [
            cmd
            for cmd in commands
            if cmd[0] == "BACKGROUND" and cmd[1] == (0, 0)
        ]
        assert len(header_bg) > 0

        # Check for header text color
        text_color = [cmd for cmd in commands if cmd[0] == "TEXTCOLOR"]
        assert len(text_color) > 0


class TestCreateConditionTable:
    """Tests for _create_condition_table function."""

    def test_creates_table_with_conditions(self):
        """Test creating table with condition data."""
        conditions = [
            Mock(num=1, expression="x > 0"),
            Mock(num=2, expression="y < 10"),
        ]

        table = _create_condition_table(conditions)

        assert isinstance(table, Table)
        # Header + 2 conditions
        assert len(table._cellvalues) == 3

    def test_table_has_correct_headers(self):
        """Test that table has correct header row."""
        conditions = []
        table = _create_condition_table(conditions)

        assert table._cellvalues[0] == ["#", "Condition"]

    def test_table_includes_condition_data(self):
        """Test that condition data is included in table."""
        conditions = [Mock(num=1, expression="x > 0")]
        table = _create_condition_table(conditions)

        assert table._cellvalues[1] == ["1", "x > 0"]

    def test_table_has_correct_column_widths(self):
        """Test that table uses correct column widths."""
        conditions = [Mock(num=1, expression="test")]
        table = _create_condition_table(conditions)

        expected = [
            PdfStyle.CONDITION_COL_NUMBER,
            PdfStyle.CONDITION_COL_TEXT,
        ]
        assert table._colWidths == expected


class TestCreateNodeTable:
    """Tests for _create_node_table function."""

    def test_creates_table_with_nodes(self):
        """Test creating table with node data."""
        nodes = [
            Mock(name="Task1", type="serviceTask", target="MyClass"),
            Mock(name="Task2", type="callActivity", target="subprocess"),
        ]

        table = _create_node_table(nodes)

        assert isinstance(table, Table)
        assert len(table._cellvalues) == 3  # Header + 2 nodes

    def test_table_has_correct_headers(self):
        """Test that table has correct header row."""
        nodes = []
        table = _create_node_table(nodes)

        assert table._cellvalues[0] == [
            "Node Name",
            "Type",
            "Called Element / Class",
        ]

    def test_table_includes_node_data(self):
        """Test that node data is included in table."""
        nodes = [Mock(name="Task1", type="serviceTask", target="MyClass")]
        # Configure Mock to return proper values for attribute access
        nodes[0].name = "Task1"
        nodes[0].type = "serviceTask"
        nodes[0].target = "MyClass"

        table = _create_node_table(nodes)

        assert table._cellvalues[1] == ["Task1", "serviceTask", "MyClass"]

    def test_table_has_correct_column_widths(self):
        """Test that table uses correct column widths."""
        nodes = [Mock(name="T", type="t", target="c")]
        table = _create_node_table(nodes)

        expected = [
            PdfStyle.NODE_COL_NAME,
            PdfStyle.NODE_COL_TYPE,
            PdfStyle.NODE_COL_DETAIL,
        ]
        assert table._colWidths == expected


class TestCreateParameterTable:
    """Tests for _create_parameter_table function."""

    def test_creates_table_with_parameters(self):
        """Test creating table with parameter data."""
        parameters = [
            Mock(
                node_name="Task1",
                param_name="p1",
                value="v1",
                has_script=False,
            ),
            Mock(
                node_name="Task2", param_name="p2", value="v2", has_script=True
            ),
        ]

        table = _create_parameter_table(parameters)

        assert isinstance(table, Table)
        assert len(table._cellvalues) == 3  # Header + 2 parameters

    def test_table_has_correct_headers(self):
        """Test that table has correct header row."""
        parameters = []
        table = _create_parameter_table(parameters)

        assert table._cellvalues[0] == [
            "Node Name",
            "Parameter Name",
            "Value",
        ]

    def test_table_includes_parameter_data(self):
        """Test that parameter data is included in table."""
        parameters = [
            Mock(
                node_name="Task1",
                param_name="p1",
                value="v1",
                has_script=False,
            )
        ]
        table = _create_parameter_table(parameters)

        assert table._cellvalues[1] == ["Task1", "p1", "v1"]

    def test_truncates_long_values(self):
        """Test that long parameter values are truncated."""
        long_value = "a" * 100
        parameters = [
            Mock(
                node_name="Task1",
                param_name="p1",
                value=long_value,
                has_script=False,
            )
        ]

        table = _create_parameter_table(parameters)
        displayed_value = table._cellvalues[1][2]

        assert len(displayed_value) == PdfStyle.MAX_VALUE_LENGTH
        assert displayed_value.endswith("...")

    def test_does_not_truncate_short_values(self):
        """Test that short values are not truncated."""
        short_value = "short"
        parameters = [
            Mock(
                node_name="Task1",
                param_name="p1",
                value=short_value,
                has_script=False,
            )
        ]

        table = _create_parameter_table(parameters)
        displayed_value = table._cellvalues[1][2]

        assert displayed_value == short_value

    def test_table_has_correct_column_widths(self):
        """Test that table uses correct column widths."""
        parameters = [
            Mock(node_name="T", param_name="p", value="v", has_script=False)
        ]
        table = _create_parameter_table(parameters)

        expected = [
            PdfStyle.PARAM_COL_NODE,
            PdfStyle.PARAM_COL_NAME,
            PdfStyle.PARAM_COL_VALUE,
        ]
        assert table._colWidths == expected


class TestCreateScriptSection:
    """Tests for _create_script_section function."""

    def test_returns_list_of_flowables(self):
        """Test that function returns a list."""
        scripts = []
        styles = getSampleStyleSheet()
        page_width = 500

        flowables = _create_script_section(scripts, styles, page_width)

        assert isinstance(flowables, list)

    def test_empty_scripts_returns_empty_list(self):
        """Test that empty scripts list returns empty flowables."""
        scripts = []
        styles = getSampleStyleSheet()

        flowables = _create_script_section(scripts, styles, 500)

        assert len(flowables) == 0

    def test_creates_flowables_for_each_script(self):
        """Test that flowables are created for each script."""
        scripts = [
            Mock(node_name="Task1", param_name="p1", text="code1"),
            Mock(node_name="Task2", param_name="p2", text="code2"),
        ]
        styles = getSampleStyleSheet()

        flowables = _create_script_section(scripts, styles, 500)

        # Each script creates: heading_table, spacer, preformatted, spacer
        # = 4 flowables per script
        assert len(flowables) == 8

    def test_flowables_contain_table_and_preformatted(self):
        """Test that flowables contain expected types."""
        scripts = [Mock(node_name="Task1", param_name="p1", text="code")]
        styles = getSampleStyleSheet()

        flowables = _create_script_section(scripts, styles, 500)

        # Should have Table, Spacer, Preformatted, Spacer
        assert isinstance(flowables[0], Table)
        assert isinstance(flowables[2], type(flowables[2]))  # Preformatted


class TestMake:
    """Tests for make function."""

    @patch("bpmn_print.pdf.SimpleDocTemplate")
    def test_creates_pdf_document(self, mock_doc_class):
        """Test that PDF document is created."""
        mock_doc = MagicMock()
        mock_doc_class.return_value = mock_doc

        with tempfile.NamedTemporaryFile(
            suffix=".png", delete=False
        ) as png_file:
            png_path = png_file.name
            # Create a minimal 1x1 PNG
            png_file.write(
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
                b"\x00\x00\x00\x01\x00\x00\x00\x01"
                b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            )

        try:
            data = PdfData(
                png_file=png_path,
                branch_conditions=[],
                nodes=[],
                parameters=[],
                jexl_scripts=[],
            )

            make("test.pdf", data)

            mock_doc_class.assert_called_once()
            mock_doc.build.assert_called_once()
        finally:
            if os.path.exists(png_path):
                os.unlink(png_path)

    @patch("bpmn_print.pdf.SimpleDocTemplate")
    def test_includes_all_sections(self, mock_doc_class):
        """Test that all sections are included when data is provided."""
        mock_doc = MagicMock()
        mock_doc_class.return_value = mock_doc

        with tempfile.NamedTemporaryFile(
            suffix=".png", delete=False
        ) as png_file:
            png_path = png_file.name
            png_file.write(
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
                b"\x00\x00\x00\x01\x00\x00\x00\x01"
                b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            )

        try:
            data = PdfData(
                png_file=png_path,
                branch_conditions=[Mock(num=1, expression="x > 0")],
                nodes=[Mock(name="T", type="serviceTask", target="C")],
                parameters=[
                    Mock(
                        node_name="T",
                        param_name="p",
                        value="v",
                        has_script=False,
                    )
                ],
                jexl_scripts=[
                    Mock(node_name="T", param_name="s", text="code")
                ],
            )

            make("test.pdf", data)

            # Check that build was called with a non-empty body
            mock_doc.build.assert_called_once()
            body = mock_doc.build.call_args[0][0]
            assert len(body) > 0
        finally:
            if os.path.exists(png_path):
                os.unlink(png_path)

    @patch("bpmn_print.pdf.SimpleDocTemplate")
    def test_handles_empty_data(self, mock_doc_class):
        """Test that make handles empty data sections."""
        mock_doc = MagicMock()
        mock_doc_class.return_value = mock_doc

        with tempfile.NamedTemporaryFile(
            suffix=".png", delete=False
        ) as png_file:
            png_path = png_file.name
            png_file.write(
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
                b"\x00\x00\x00\x01\x00\x00\x00\x01"
                b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            )

        try:
            data = PdfData(
                png_file=png_path,
                branch_conditions=[],
                nodes=[],
                parameters=[],
                jexl_scripts=[],
            )

            make("test.pdf", data)

            # Should still build successfully with just diagram
            mock_doc.build.assert_called_once()
        finally:
            if os.path.exists(png_path):
                os.unlink(png_path)
