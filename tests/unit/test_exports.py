from io import BytesIO
from zipfile import ZipFile

import pytest

from apps.api.services.exporter import (
    MIME_TYPES,
    ExportCitation,
    ExportContent,
    ExportMetric,
    build_export,
    safe_filename,
)


@pytest.fixture
def export_content() -> ExportContent:
    return ExportContent(
        title="Pump discharge pressure review",
        content=(
            "## Recommendation\n"
            "Maintain the current operating limit.\n"
            "- Verify the pressure indicator before startup.\n"
            "- Record the reading in the shift log."
        ),
        user_id="operator-01",
        role="PROCESS_ENGINEER",
        thread_id="thread-123",
        citations=[
            ExportCitation(
                document="OISD-118",
                section="Section 7.2",
                excerpt="Verify isolation before maintenance.",
                score=0.94,
            )
        ],
        metrics=[ExportMetric(name="Pressure drop", value="42.5 kPa")],
        calculation_output="Pressure drop = 42.5 kPa",
        calculation_script="print(42.5)",
    )


@pytest.mark.parametrize(
    ("export_format", "required_member"),
    [
        ("docx", "word/document.xml"),
        ("pptx", "ppt/presentation.xml"),
        ("xlsx", "xl/workbook.xml"),
    ],
)
def test_build_export_creates_valid_office_package(
    export_content: ExportContent,
    export_format: str,
    required_member: str,
):
    data = build_export(export_content, export_format)
    assert data.startswith(b"PK")
    with ZipFile(BytesIO(data)) as package:
        assert required_member in package.namelist()


def test_safe_filename_removes_unsafe_characters():
    assert safe_filename("../../Pump Review: A/B", "docx") == "pump-review-a-b.docx"


def test_all_export_formats_have_office_mime_types():
    assert set(MIME_TYPES) == {"docx", "pptx", "xlsx"}
    assert all(value.startswith("application/") for value in MIME_TYPES.values())
