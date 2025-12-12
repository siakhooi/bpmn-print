import os
from dataclasses import dataclass

from bpmn_print import console
from . import bpmn_diagram
from . import bpmn_data
from . import pdf


@dataclass
class ConversionConfig:
    """Configuration for BPMN to PDF conversion.

    Groups file paths and options for the conversion process,
    reducing parameter count in convert_bpmn_to_pdf function.

    Attributes:
        bpmn_file: Path to the input BPMN file
        pdf_path: Path to the output PDF file
        png_file: Path to the intermediate PNG file for the diagram
        keep_png: Whether to keep the PNG file after PDF generation
    """
    bpmn_file: str
    pdf_path: str
    png_file: str
    keep_png: bool = False


def convert_bpmn_to_pdf(config: ConversionConfig) -> None:
    """
    Convert a BPMN file to a pretty-printed PDF document.

    Args:
        config: ConversionConfig with all file paths and conversion options
    """
    # 1. Render diagram to PNG
    branch_conditions = bpmn_diagram.render(config.bpmn_file, config.png_file)

    # 2. Extract data
    nodes, parameters, jexl_scripts = bpmn_data.extract(config.bpmn_file)

    # 3. Create PDF with grouped data
    pdf_data = pdf.PdfData(
        png_file=config.png_file,
        branch_conditions=branch_conditions,
        nodes=nodes,
        parameters=parameters,
        jexl_scripts=jexl_scripts
    )
    pdf.make(config.pdf_path, pdf_data)

    # 4. Remove PNG file if not keeping it
    if not config.keep_png and os.path.exists(config.png_file):
        try:
            os.remove(config.png_file)
        except OSError as e:
            console.warning(
                f"Could not remove PNG file {config.png_file}: {e}"
            )


def pretty_print(
    input_folder: str, output_folder: str, keep_png: bool = False
) -> None:
    os.makedirs(output_folder, exist_ok=True)

    # Collect BPMN files to process
    bpmn_files = [f for f in os.listdir(input_folder) if f.endswith(".bpmn")]

    if not bpmn_files:
        console.info(f"No BPMN files found in {input_folder}")
        return

    console.info(f"Found {len(bpmn_files)} BPMN file(s) to process")

    for file in bpmn_files:
        console.info(f"Processing {file}...")
        src_bpmn_file = os.path.join(input_folder, file)
        dest_pdf_path = os.path.join(
            output_folder, file.replace(".bpmn", ".pdf")
        )
        png_file = dest_pdf_path.replace(".pdf", ".png")
        config = ConversionConfig(
            bpmn_file=src_bpmn_file,
            pdf_path=dest_pdf_path,
            png_file=png_file,
            keep_png=keep_png
        )
        convert_bpmn_to_pdf(config)
        console.info(f"✓ Generated {dest_pdf_path}")

    console.println("Done.")
