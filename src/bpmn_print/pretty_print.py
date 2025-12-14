import os
from dataclasses import dataclass
from pathlib import Path

from bpmn_print import console
from . import bpmn_diagram
from . import bpmn_data
from . import pdf
from .errors import BpmnRenderError, BpmnFileError
from .xml_utils import create_bpmn_context

# File extension constants
BPMN_EXTENSION = ".bpmn"
PDF_EXTENSION = ".pdf"
PNG_EXTENSION = ".png"


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
        landscape_threshold: Width threshold in pixels for landscape layout
    """

    bpmn_file: str
    pdf_path: str
    png_file: str
    keep_png: bool = False
    landscape_threshold: int = 2200


def convert_bpmn_to_pdf(config: ConversionConfig) -> None:
    """
    Convert a BPMN file to a pretty-printed PDF document.

    Args:
        config: ConversionConfig with all file paths and conversion options
    """
    # Parse XML once and create shared context
    context = create_bpmn_context(config.bpmn_file)

    # 1. Render diagram to PNG using the shared context
    branch_conditions = bpmn_diagram.render(context, config.png_file)

    # 2. Extract data using the same shared context (avoids re-parsing)
    result = bpmn_data.extract(context)

    # 3. Create PDF with grouped data
    pdf_data = pdf.PdfData(
        png_file=config.png_file,
        branch_conditions=branch_conditions,
        nodes=result.nodes,
        parameters=result.parameters,
        jexl_scripts=result.scripts,
    )
    pdf.make(config.pdf_path, pdf_data, config.landscape_threshold)

    # 4. Remove PNG file if not keeping it
    if not config.keep_png and os.path.exists(config.png_file):
        try:
            os.remove(config.png_file)
        except OSError as e:
            console.warning(
                f"Could not remove PNG file {config.png_file}: {e}"
            )


def pretty_print(
    input_folder: str,
    output_folder: str,
    keep_png: bool = False,
    landscape_threshold: int = 2200,
) -> None:
    output_path = Path(output_folder)
    # Create output folder with error handling
    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise BpmnRenderError.output_dir_error(output_folder, str(e)) from e

    input_path = Path(input_folder)
    # Collect BPMN files to process with error handling
    try:
        bpmn_files = [f.name for f in input_path.glob(f"*{BPMN_EXTENSION}")]
    except OSError as e:
        raise BpmnFileError.not_readable(input_folder, str(e)) from e

    if not bpmn_files:
        console.info(f"No BPMN files found in {input_folder}")
        return

    console.info(f"Found {len(bpmn_files)} BPMN file(s) to process")

    for file in bpmn_files:
        console.info(f"Processing {file}...")
        src_bpmn_file = str(input_path / file)
        dest_pdf_path = output_path / file.replace(
            BPMN_EXTENSION, PDF_EXTENSION
        )
        png_file = dest_pdf_path.with_suffix(PNG_EXTENSION)

        config = ConversionConfig(
            bpmn_file=src_bpmn_file,
            pdf_path=str(dest_pdf_path),
            png_file=str(png_file),
            keep_png=keep_png,
            landscape_threshold=landscape_threshold,
        )
        convert_bpmn_to_pdf(config)
        console.info(f"✓ Generated {dest_pdf_path}")

    console.println("Done.")
