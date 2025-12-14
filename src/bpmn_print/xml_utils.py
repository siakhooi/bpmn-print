from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from lxml import etree
from lxml.etree import _Element, XMLSyntaxError

from .errors import BpmnFileError, BpmnParseError
from .xml_constants import ATTR_ID, ATTR_NAME, XPATH_ALL_WITH_ID


def parse_bpmn_xml(xml_file: str) -> _Element:
    """Parse a BPMN XML file and return the root element."""
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


def build_id_to_name_mapping(root: _Element) -> Dict[str, str]:
    """Build a mapping from element IDs to their names.

    This function searches for all elements with an "id" attribute in the
    XML tree, regardless of namespace.

    Returns:
        Dictionary mapping element IDs to their names
        (or IDs if no name exists)
    """
    return {
        elem.get(ATTR_ID): elem.get(ATTR_NAME, elem.get(ATTR_ID))
        for elem in root.findall(XPATH_ALL_WITH_ID)
    }


@dataclass
class BpmnContext:

    root: _Element
    id_to_name: Dict[str, str]


def create_bpmn_context(xml_file: str) -> BpmnContext:
    root = parse_bpmn_xml(xml_file)
    id_to_name = build_id_to_name_mapping(root)
    return BpmnContext(root=root, id_to_name=id_to_name)
