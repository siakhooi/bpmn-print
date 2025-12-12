"""Shared XML parsing utilities for BPMN files.

This module provides common XML parsing functionality used across
the bpmn_print package to avoid code duplication.
"""

from pathlib import Path
from typing import Dict, Tuple

from lxml import etree
from lxml.etree import _Element, XMLSyntaxError

from .errors import BpmnFileError, BpmnParseError
from .xml_constants import ATTR_ID, ATTR_NAME, XPATH_ALL_WITH_ID


def parse_bpmn_xml(xml_file: str) -> _Element:
    """Parse a BPMN XML file and return the root element.

    This function provides standardized XML parsing with consistent
    error handling for BPMN files. It validates the file exists and
    is readable before parsing.

    Args:
        xml_file: Path to the BPMN XML file

    Returns:
        Root element of the parsed XML tree

    Raises:
        BpmnFileError: If the XML file does not exist, is not a file,
            or cannot be read
        BpmnParseError: If the XML file is malformed or invalid
    """
    # Check if file exists before attempting to parse
    file_path = Path(xml_file)
    if not file_path.exists():
        raise BpmnFileError.not_found(xml_file)

    if not file_path.is_file():
        raise BpmnFileError.not_a_file(xml_file)

    try:
        tree = etree.parse(xml_file)
    except OSError as e:
        raise BpmnFileError.not_readable(xml_file, str(e)) from e
    except XMLSyntaxError as e:
        raise BpmnParseError.invalid_xml(xml_file, str(e)) from e

    return tree.getroot()


def parse_bpmn_xml_with_namespace(
    xml_file: str, namespace: Dict[str, str]
) -> Tuple[_Element, Dict[str, str]]:
    """Parse a BPMN XML file and return root element with namespace mapping.

    This is a convenience function for cases where the namespace mapping
    needs to be returned alongside the root element.

    Args:
        xml_file: Path to the BPMN XML file
        namespace: Namespace mapping dictionary to return

    Returns:
        Tuple of (root_element, namespace_dict) for XPath queries

    Raises:
        BpmnFileError: If the XML file does not exist, is not a file,
            or cannot be read
        BpmnParseError: If the XML file is malformed or invalid
    """
    root = parse_bpmn_xml(xml_file)
    return root, namespace


def build_id_to_name_mapping(root: _Element) -> Dict[str, str]:
    """Build a mapping from element IDs to their names.

    This function searches for all elements with an "id" attribute in the
    XML tree, regardless of namespace. This is intentional because:
    1. BPMN elements may have IDs
    2. Other XML elements (e.g., from extensions) may also have IDs
    3. We need to map all IDs to names for reference resolution

    Note: This XPath query (".//*[@id]") intentionally does not use the
    BPMN namespace prefix because we want to find ALL elements with IDs,
    not just BPMN elements.

    Args:
        root: Root element of the BPMN XML tree

    Returns:
        Dictionary mapping element IDs to their names
        (or IDs if no name exists)
    """
    return {
        elem.get(ATTR_ID): elem.get(ATTR_NAME, elem.get(ATTR_ID))
        for elem in root.findall(XPATH_ALL_WITH_ID)
    }
