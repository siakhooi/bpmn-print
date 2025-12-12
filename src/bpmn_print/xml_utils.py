"""Shared XML parsing utilities for BPMN files.

This module provides common XML parsing functionality used across
the bpmn_print package to avoid code duplication.
"""

from pathlib import Path
from typing import Tuple

from lxml import etree
from lxml.etree import _Element, XMLSyntaxError


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
        FileNotFoundError: If the XML file does not exist or cannot be read
        ValueError: If the path is not a file
        XMLSyntaxError: If the XML file is malformed or invalid
    """
    # Check if file exists before attempting to parse
    file_path = Path(xml_file)
    if not file_path.exists():
        raise FileNotFoundError(
            f"BPMN file not found: {xml_file}"
        )

    if not file_path.is_file():
        raise ValueError(
            f"Path is not a file: {xml_file}"
        )

    try:
        tree = etree.parse(xml_file)
    except OSError as e:
        raise FileNotFoundError(
            f"BPMN file cannot be read: {xml_file}"
        ) from e
    except XMLSyntaxError as e:
        raise XMLSyntaxError(
            f"Invalid XML syntax in BPMN file: {xml_file}"
        ) from e

    return tree.getroot()


def parse_bpmn_xml_with_namespace(
    xml_file: str, namespace: dict
) -> Tuple[_Element, dict]:
    """Parse a BPMN XML file and return root element with namespace mapping.

    This is a convenience function for cases where the namespace mapping
    needs to be returned alongside the root element.

    Args:
        xml_file: Path to the BPMN XML file
        namespace: Namespace mapping dictionary to return

    Returns:
        Tuple of (root_element, namespace_dict) for XPath queries

    Raises:
        FileNotFoundError: If the XML file does not exist or cannot be read
        ValueError: If the path is not a file
        XMLSyntaxError: If the XML file is malformed or invalid
    """
    root = parse_bpmn_xml(xml_file)
    return root, namespace
