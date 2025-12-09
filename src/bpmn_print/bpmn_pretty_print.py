import os

from bpmn_print import console
from . import bpmn_diagram
from . import bpmn_data
from . import pdf


def convert_bpmn_to_pdf(
    bpmn_file: str, pdf_path: str, png_file: str, keep_png: bool = False
) -> None:
    """
    Convert a BPMN file to a pretty-printed PDF document.

    Args:
        bpmn_file (str): Path to the input BPMN file.
        pdf_path (str): Path to the output PDF file.
        png_file (str): Path to the intermediate PNG file for the diagram.
        keep_png (bool): Whether to keep the PNG file after PDF generation.
    """
    # 1. Render diagram to PNG
    branch_conditions = bpmn_diagram.render(bpmn_file, png_file)

    # 2. Extract data
    nodes, parameters, jexl_scripts = bpmn_data.extract(bpmn_file)

    # 3. Create PDF
    pdf.make(
        pdf_path, png_file, branch_conditions, nodes, parameters,
        jexl_scripts
    )

    # 4. Remove PNG file if not keeping it
    if not keep_png and os.path.exists(png_file):
        os.remove(png_file)


def pretty_print(
    input_folder: str, output_folder: str, keep_png: bool = False
) -> None:
    os.makedirs(output_folder, exist_ok=True)

    for file in os.listdir(input_folder):
        if file.endswith(".bpmn"):
            src_bpmn_file = os.path.join(input_folder, file)
            dest_pdf_path = os.path.join(
                output_folder, file.replace(".bpmn", ".pdf")
            )
            png_file = dest_pdf_path.replace(".pdf", ".png")
            convert_bpmn_to_pdf(
                src_bpmn_file, dest_pdf_path, png_file, keep_png
            )
    console.println("Done.")
