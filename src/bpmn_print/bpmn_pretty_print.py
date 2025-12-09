import os

from bpmn_print import console
from . import bpmn_diagram
from . import bpmn_data
from . import pdf


def convert_bpmn_to_pdf(bpmn_file: str, pdf_path: str) -> None:
    """
    Convert a BPMN file to a pretty-printed PDF document.

    Args:
        bpmn_file (str): Path to the input BPMN file.
        pdf_path (str): Path to the output PDF file.
    """
    # 1. Render diagram to PNG
    png_file = pdf_path.replace(".pdf", ".png")
    branch_conditions = bpmn_diagram.render(bpmn_file, png_file)

    # 2. Extract data
    nodes, parameters, jexl_scripts = bpmn_data.extract(bpmn_file)

    # 3. Create PDF
    pdf.make(
        pdf_path, png_file, branch_conditions, nodes, parameters,
        jexl_scripts
    )


def pretty_print(input_folder: str, output_folder: str) -> None:
    os.makedirs(output_folder, exist_ok=True)

    for file in os.listdir(input_folder):
        if file.endswith(".bpmn"):
            src = os.path.join(input_folder, file)
            dest = os.path.join(output_folder, file.replace(".bpmn", ".pdf"))
            convert_bpmn_to_pdf(src, dest)
    console.println("Done.")
