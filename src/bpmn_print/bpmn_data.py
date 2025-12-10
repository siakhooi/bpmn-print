from dataclasses import dataclass
from lxml import etree

# BPMN namespace constants
BPMN_NS = {
    "camunda": "http://camunda.org/schema/1.0/bpmn",
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"
}
CAMUNDA_CLASS_ATTR = '{http://camunda.org/schema/1.0/bpmn}class'


@dataclass
class Node:
    """Represents a BPMN node (callActivity or serviceTask)."""
    name: str
    type: str
    target: str

    def __iter__(self):
        """Allow tuple unpacking for backward compatibility."""
        return iter((self.name, self.type, self.target))


@dataclass
class Parameter:
    """Represents an input parameter."""
    node_name: str
    param_name: str
    value: str
    has_script: bool

    def __iter__(self):
        """Allow tuple unpacking for backward compatibility."""
        return iter((
            self.node_name, self.param_name, self.value, self.has_script
        ))


@dataclass
class Script:
    """Represents a JEXL script."""
    text: str
    node_name: str
    param_name: str

    def __iter__(self):
        """Allow tuple unpacking for backward compatibility."""
        return iter((self.text, self.node_name, self.param_name))


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


def extract(xml_file):
    tree = etree.parse(xml_file)
    root = tree.getroot()

    # Create ID to name mapping for all elements
    id_to_name = {}
    for elem in root.findall(".//*[@id]"):
        elem_id = elem.get('id')
        elem_name = elem.get('name', elem_id)
        id_to_name[elem_id] = elem_name

    # Collect node information (callActivity and serviceTask)
    nodes = []

    # Find all callActivity elements
    for call_activity in root.findall(".//bpmn:callActivity", BPMN_NS):
        node_name = call_activity.get(
            'name', call_activity.get('id', 'unknown')
        )
        called_element = call_activity.get('calledElement', '')
        nodes.append(Node(node_name, 'callActivity', called_element))

    # Find all serviceTask elements
    for service_task in root.findall(".//bpmn:serviceTask", BPMN_NS):
        node_name = service_task.get(
            'name', service_task.get('id', 'unknown')
        )
        class_name = service_task.get(CAMUNDA_CLASS_ATTR, '')
        # Simplify class name - show only the last part
        simple_class = class_name.split('.')[-1] if class_name else ''
        nodes.append(Node(node_name, 'serviceTask', simple_class))

    parameters = []
    scripts = []

    # All script elements
    for scr in root.findall(".//camunda:script", BPMN_NS):
        node_id = find_parent_with_id(scr)
        node_name = id_to_name.get(node_id, node_id)
        param_name = scr.getparent().get('name', 'script')
        scripts.append(Script(scr.text or "", node_name, param_name))

    # inputOutput mappings - collect all inputParameters
    for inp in root.findall(".//camunda:inputParameter", BPMN_NS):
        node_id = find_parent_with_id(inp)
        node_name = id_to_name.get(node_id, node_id)
        param_name = inp.get('name', 'inputParameter')

        # Check if it contains a script element
        script_elem = inp.find(".//camunda:script", BPMN_NS)
        if script_elem is not None:
            # Has script - will be shown in scripts section
            parameters.append(
                Parameter(node_name, param_name, '[See JEXL Scripts]', True)
            )
        elif inp.text:
            # Has text content
            if "#{ " in inp.text or "${ " in inp.text:
                # JEXL expression - add to scripts
                scripts.append(Script(inp.text, node_name, param_name))
                parameters.append(
                    Parameter(
                        node_name, param_name, '[See JEXL Scripts]', True
                    )
                )
            else:
                # Simple value
                parameters.append(
                    Parameter(node_name, param_name, inp.text, False)
                )
        else:
            # Empty or other
            parameters.append(Parameter(node_name, param_name, '', False))

    return nodes, parameters, scripts
