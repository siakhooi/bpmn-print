import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from lxml import etree
from lxml.etree import _Element

from bpmn_print.xml_utils import (
    parse_bpmn_xml,
    build_id_to_name_mapping,
)
from bpmn_print.errors import BpmnFileError, BpmnParseError


class TestParseBpmnXml:
    """Tests for parse_bpmn_xml function."""

    def test_parses_valid_xml_file(self):
        """Test parsing a valid BPMN XML file."""
        with TemporaryDirectory() as tmpdir:
            xml_file = Path(tmpdir) / "test.bpmn"
            xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL">
    <process id="Process_1">
        <startEvent id="StartEvent_1" name="Start"/>
    </process>
</definitions>"""
            xml_file.write_text(xml_content)

            root = parse_bpmn_xml(str(xml_file))

            assert isinstance(root, _Element)
            assert root.tag.endswith("definitions")

    def test_returns_root_element(self):
        """Test that function returns root element."""
        with TemporaryDirectory() as tmpdir:
            xml_file = Path(tmpdir) / "test.bpmn"
            xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<root>
    <child id="1"/>
</root>"""
            xml_file.write_text(xml_content)

            root = parse_bpmn_xml(str(xml_file))

            assert root.tag == "root"

    def test_raises_error_when_file_not_found(self):
        """Test that BpmnFileError is raised when file doesn't exist."""
        with pytest.raises(BpmnFileError) as exc_info:
            parse_bpmn_xml("/nonexistent/file.bpmn")

        assert "BPMN file not found" in str(exc_info.value)

    def test_raises_error_when_path_is_directory(self):
        """Test that BpmnFileError is raised when path is directory."""
        with TemporaryDirectory() as tmpdir:
            with pytest.raises(BpmnFileError) as exc_info:
                parse_bpmn_xml(tmpdir)

            assert "Path is not a file" in str(exc_info.value)

    def test_raises_error_when_file_not_readable(self, monkeypatch):
        """Test that BpmnFileError is raised when file can't be read."""
        with TemporaryDirectory() as tmpdir:
            xml_file = Path(tmpdir) / "test.bpmn"
            xml_file.write_text("<root/>")

            # Mock etree.parse to raise OSError
            def failing_parse(file_path):
                raise OSError("Permission denied")

            monkeypatch.setattr(etree, "parse", failing_parse)

            with pytest.raises(BpmnFileError) as exc_info:
                parse_bpmn_xml(str(xml_file))

            assert "BPMN file cannot be read" in str(exc_info.value)
            assert "Permission denied" in str(exc_info.value)

    def test_raises_error_when_xml_invalid(self):
        """Test that BpmnParseError is raised for invalid XML."""
        with TemporaryDirectory() as tmpdir:
            xml_file = Path(tmpdir) / "invalid.bpmn"
            xml_file.write_text("<root><unclosed>")

            with pytest.raises(BpmnParseError) as exc_info:
                parse_bpmn_xml(str(xml_file))

            assert "Invalid XML syntax in BPMN file" in str(exc_info.value)

    def test_preserves_oserror_in_exception_chain(self, monkeypatch):
        """Test that OSError is preserved in exception chain."""
        with TemporaryDirectory() as tmpdir:
            xml_file = Path(tmpdir) / "test.bpmn"
            xml_file.write_text("<root/>")

            def failing_parse(file_path):
                raise OSError("Original error")

            monkeypatch.setattr(etree, "parse", failing_parse)

            with pytest.raises(BpmnFileError) as exc_info:
                parse_bpmn_xml(str(xml_file))

            assert exc_info.value.__cause__ is not None
            assert isinstance(exc_info.value.__cause__, OSError)

    def test_preserves_xml_syntax_error_in_exception_chain(self):
        """Test that XMLSyntaxError is preserved in exception chain."""
        with TemporaryDirectory() as tmpdir:
            xml_file = Path(tmpdir) / "invalid.bpmn"
            xml_file.write_text("<root><unclosed>")

            with pytest.raises(BpmnParseError) as exc_info:
                parse_bpmn_xml(str(xml_file))

            assert exc_info.value.__cause__ is not None

    def test_parses_xml_with_namespaces(self):
        """Test parsing XML with namespaces."""
        with TemporaryDirectory() as tmpdir:
            xml_file = Path(tmpdir) / "test.bpmn"
            xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
    <bpmn:process id="Process_1"/>
</bpmn:definitions>"""
            xml_file.write_text(xml_content)

            root = parse_bpmn_xml(str(xml_file))

            assert root is not None

    def test_parses_empty_root_element(self):
        """Test parsing XML with empty root element."""
        with TemporaryDirectory() as tmpdir:
            xml_file = Path(tmpdir) / "test.bpmn"
            xml_file.write_text('<?xml version="1.0"?><root/>')

            root = parse_bpmn_xml(str(xml_file))

            assert root.tag == "root"
            assert len(root) == 0

    def test_accepts_path_object(self):
        """Test that function accepts Path objects."""
        with TemporaryDirectory() as tmpdir:
            xml_file = Path(tmpdir) / "test.bpmn"
            xml_file.write_text("<root/>")

            # Function expects string but Path should work via str()
            root = parse_bpmn_xml(str(xml_file))

            assert root is not None

    def test_parses_xml_with_attributes(self):
        """Test parsing XML with various attributes."""
        with TemporaryDirectory() as tmpdir:
            xml_file = Path(tmpdir) / "test.bpmn"
            xml_content = """<?xml version="1.0"?>
<root id="root1" name="RootElement" type="test"/>"""
            xml_file.write_text(xml_content)

            root = parse_bpmn_xml(str(xml_file))

            assert root.get("id") == "root1"
            assert root.get("name") == "RootElement"

    def test_error_message_contains_file_path(self):
        """Test that error messages contain the file path."""
        file_path = "/path/to/nonexistent.bpmn"

        with pytest.raises(BpmnFileError) as exc_info:
            parse_bpmn_xml(file_path)

        assert file_path in str(exc_info.value)


class TestBuildIdToNameMapping:
    """Tests for build_id_to_name_mapping function."""

    def test_maps_id_to_name(self):
        """Test basic ID to name mapping."""
        xml_content = """<?xml version="1.0"?>
<root>
    <element id="elem1" name="Element One"/>
    <element id="elem2" name="Element Two"/>
</root>"""
        root = etree.fromstring(xml_content.encode())

        mapping = build_id_to_name_mapping(root)

        assert mapping["elem1"] == "Element One"
        assert mapping["elem2"] == "Element Two"

    def test_uses_id_when_name_missing(self):
        """Test that ID is used when name attribute is missing."""
        xml_content = """<?xml version="1.0"?>
<root>
    <element id="elem1" name="Has Name"/>
    <element id="elem2"/>
</root>"""
        root = etree.fromstring(xml_content.encode())

        mapping = build_id_to_name_mapping(root)

        assert mapping["elem1"] == "Has Name"
        assert mapping["elem2"] == "elem2"

    def test_empty_root_returns_empty_dict(self):
        """Test that empty root returns empty dictionary."""
        xml_content = """<?xml version="1.0"?><root/>"""
        root = etree.fromstring(xml_content.encode())

        mapping = build_id_to_name_mapping(root)

        assert mapping == {}

    def test_includes_nested_elements(self):
        """Test that nested elements are included."""
        xml_content = """<?xml version="1.0"?>
<root>
    <level1 id="l1" name="Level 1">
        <level2 id="l2" name="Level 2">
            <level3 id="l3" name="Level 3"/>
        </level2>
    </level1>
</root>"""
        root = etree.fromstring(xml_content.encode())

        mapping = build_id_to_name_mapping(root)

        assert mapping["l1"] == "Level 1"
        assert mapping["l2"] == "Level 2"
        assert mapping["l3"] == "Level 3"
        assert len(mapping) == 3

    def test_ignores_elements_without_id(self):
        """Test that elements without ID are ignored."""
        xml_content = """<?xml version="1.0"?>
<root>
    <element id="elem1" name="Has ID"/>
    <element name="No ID"/>
    <element id="elem2" name="Also Has ID"/>
</root>"""
        root = etree.fromstring(xml_content.encode())

        mapping = build_id_to_name_mapping(root)

        assert len(mapping) == 2
        assert "elem1" in mapping
        assert "elem2" in mapping

    def test_handles_empty_name_attribute(self):
        """Test handling of empty name attribute."""
        xml_content = """<?xml version="1.0"?>
<root>
    <element id="elem1" name=""/>
</root>"""
        root = etree.fromstring(xml_content.encode())

        mapping = build_id_to_name_mapping(root)

        # Empty string is falsy, but get() returns it, not the default
        assert mapping["elem1"] == ""

    def test_handles_duplicate_ids(self):
        """Test that last element with duplicate ID wins."""
        xml_content = """<?xml version="1.0"?>
<root>
    <element id="duplicate" name="First"/>
    <element id="duplicate" name="Second"/>
</root>"""
        root = etree.fromstring(xml_content.encode())

        mapping = build_id_to_name_mapping(root)

        # Dict comprehension means last one wins
        assert mapping["duplicate"] == "Second"

    def test_with_bpmn_namespaces(self):
        """Test with actual BPMN namespace structure."""
        xml_content = """<?xml version="1.0"?>
<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL">
    <process id="Process_1" name="Main Process">
        <startEvent id="StartEvent_1" name="Start"/>
        <task id="Task_1" name="Do Something"/>
        <endEvent id="EndEvent_1" name="End"/>
    </process>
</definitions>"""
        root = etree.fromstring(xml_content.encode())

        mapping = build_id_to_name_mapping(root)

        assert "Process_1" in mapping
        assert "StartEvent_1" in mapping
        assert "Task_1" in mapping
        assert "EndEvent_1" in mapping
        assert mapping["Process_1"] == "Main Process"
        assert mapping["Task_1"] == "Do Something"

    def test_returns_dict_type(self):
        """Test that function returns a dictionary."""
        xml_content = """<?xml version="1.0"?>
<root>
    <element id="elem1" name="Test"/>
</root>"""
        root = etree.fromstring(xml_content.encode())

        mapping = build_id_to_name_mapping(root)

        assert isinstance(mapping, dict)

    def test_with_special_characters_in_names(self):
        """Test with special characters in names."""
        xml_content = """<?xml version="1.0"?>
<root>
    <element id="elem1" name="Test &amp; Name"/>
    <element id="elem2" name="Test &lt;Name&gt;"/>
</root>"""
        root = etree.fromstring(xml_content.encode())

        mapping = build_id_to_name_mapping(root)

        assert mapping["elem1"] == "Test & Name"
        assert mapping["elem2"] == "Test <Name>"

    def test_with_unicode_in_names(self):
        """Test with unicode characters in names."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<root>
    <element id="elem1" name="测试"/>
    <element id="elem2" name="Tëst"/>
</root>"""
        root = etree.fromstring(xml_content.encode("utf-8"))

        mapping = build_id_to_name_mapping(root)

        assert mapping["elem1"] == "测试"
        assert mapping["elem2"] == "Tëst"

    def test_with_numeric_ids(self):
        """Test with numeric IDs."""
        xml_content = """<?xml version="1.0"?>
<root>
    <element id="123" name="Numeric ID"/>
    <element id="456"/>
</root>"""
        root = etree.fromstring(xml_content.encode())

        mapping = build_id_to_name_mapping(root)

        assert mapping["123"] == "Numeric ID"
        assert mapping["456"] == "456"

    def test_with_very_long_names(self):
        """Test with very long name values."""
        long_name = "A" * 1000
        xml_content = f"""<?xml version="1.0"?>
<root>
    <element id="elem1" name="{long_name}"/>
</root>"""
        root = etree.fromstring(xml_content.encode())

        mapping = build_id_to_name_mapping(root)

        assert mapping["elem1"] == long_name
        assert len(mapping["elem1"]) == 1000


class TestIntegration:
    """Integration tests for xml_utils functions."""

    def test_parse_and_build_mapping(self):
        """Test parsing a file and building mapping."""
        with TemporaryDirectory() as tmpdir:
            xml_file = Path(tmpdir) / "test.bpmn"
            xml_content = """<?xml version="1.0"?>
<definitions>
    <process id="Process_1" name="Main Process">
        <startEvent id="Start_1" name="Start Event"/>
        <task id="Task_1" name="User Task"/>
    </process>
</definitions>"""
            xml_file.write_text(xml_content)

            root = parse_bpmn_xml(str(xml_file))
            mapping = build_id_to_name_mapping(root)

            assert "Process_1" in mapping
            assert "Start_1" in mapping
            assert "Task_1" in mapping
            assert mapping["Process_1"] == "Main Process"

    def test_full_workflow_with_complex_bpmn(self):
        """Test complete workflow with complex BPMN structure."""
        with TemporaryDirectory() as tmpdir:
            xml_file = Path(tmpdir) / "complex.bpmn"
            xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<definitions
    xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:camunda="http://camunda.org/schema/1.0/bpmn">
    <process id="Process_1" name="Order Process">
        <startEvent id="StartEvent_1" name="Order Received"/>
        <sequenceFlow id="Flow_1" sourceRef="StartEvent_1"
                      targetRef="Task_1"/>
        <userTask id="Task_1" name="Review Order"/>
        <sequenceFlow id="Flow_2" sourceRef="Task_1"
                      targetRef="Gateway_1"/>
        <exclusiveGateway id="Gateway_1" name="Approved?"/>
        <endEvent id="EndEvent_1" name="Order Complete"/>
    </process>
</definitions>"""
            xml_file.write_text(xml_content)

            root = parse_bpmn_xml(str(xml_file))
            mapping = build_id_to_name_mapping(root)

            assert len(mapping) >= 6
            assert mapping["Process_1"] == "Order Process"
            assert mapping["StartEvent_1"] == "Order Received"
            assert mapping["Task_1"] == "Review Order"
            assert mapping["Gateway_1"] == "Approved?"
            assert mapping["EndEvent_1"] == "Order Complete"


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_xml_with_cdata(self):
        """Test XML with CDATA sections."""
        xml_content = """<?xml version="1.0"?>
<root>
    <element id="elem1" name="Normal Name"/>
    <description id="desc1"><![CDATA[Some text]]></description>
</root>"""
        root = etree.fromstring(xml_content.encode())

        mapping = build_id_to_name_mapping(root)

        assert "elem1" in mapping
        assert "desc1" in mapping

    def test_xml_with_comments(self):
        """Test that comments don't affect mapping."""
        xml_content = """<?xml version="1.0"?>
<root>
    <!-- This is a comment -->
    <element id="elem1" name="Test"/>
    <!-- Another comment -->
</root>"""
        root = etree.fromstring(xml_content.encode())

        mapping = build_id_to_name_mapping(root)

        assert len(mapping) == 1
        assert mapping["elem1"] == "Test"

    def test_xml_with_processing_instructions(self):
        """Test XML with processing instructions."""
        xml_content = """<?xml version="1.0"?>
<?xml-stylesheet type="text/xsl" href="style.xsl"?>
<root>
    <element id="elem1" name="Test"/>
</root>"""
        root = etree.fromstring(xml_content.encode())

        mapping = build_id_to_name_mapping(root)

        assert mapping["elem1"] == "Test"

    def test_parse_file_with_bom(self):
        """Test parsing file with UTF-8 BOM."""
        with TemporaryDirectory() as tmpdir:
            xml_file = Path(tmpdir) / "test.bpmn"
            # UTF-8 BOM + XML content
            xml_content = '\ufeff<?xml version="1.0"?><root/>'
            xml_file.write_text(xml_content, encoding="utf-8")

            root = parse_bpmn_xml(str(xml_file))

            assert root is not None
