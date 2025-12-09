from lxml import etree


def extract(xml_file):
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
