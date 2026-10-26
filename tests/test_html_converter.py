"""Unit and integration tests for mineru_html_converter."""

from pathlib import Path
import pytest
from click.testing import CliRunner

from mineru_html_converter.cli.app import cli
from mineru_html_converter.config.constants import RenderModeEnum, ThemeEnum
from mineru_html_converter.config.settings import HTMLConversionConfig
from mineru_html_converter.core.converter import MinerUHTMLConverter
from mineru_html_converter.exporters.postprocessor import embed_images_as_base64, inject_theme_and_toc


def test_config_defaults():
    config = HTMLConversionConfig()
    assert config.mode == RenderModeEnum.DEFAULT
    assert config.theme == ThemeEnum.MODERN
    assert config.embed_images is True
    assert config.add_toc is True


def test_postprocessor_theme_and_toc():
    sample_html = """<!doctype html>
<html>
<head><title>Test</title></head>
<body>
<h1>Introduction</h1>
<p>Some text</p>
<h2>Background</h2>
<p>More text</p>
</body>
</html>"""
    enhanced = inject_theme_and_toc(sample_html, theme="dark", add_toc=True, title="Custom Title")
    assert "mineru-theme-style" in enhanced
    assert "mineru-toc-nav" in enhanced
    assert "Introduction" in enhanced
    assert "Custom Title" in enhanced


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "MinerU Document to HTML Converter" in result.output
    assert "convert" in result.output
    assert "batch" in result.output


def test_cli_convert_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["convert", "--help"])
    assert result.exit_code == 0
    assert "--output" in result.output
    assert "--theme" in result.output
    assert "--embed-images" in result.output


def test_docx_conversion(tmp_path):
    import docx
    doc = docx.Document()
    doc.add_heading("Docx Test Heading", level=1)
    doc.add_paragraph("Paragraph inside docx document.")
    docx_file = tmp_path / "sample.docx"
    doc.save(docx_file)

    converter = MinerUHTMLConverter()
    out_html = tmp_path / "sample_docx.html"
    res = converter.convert(docx_file, output_path=out_html)

    assert res.success is True
    assert out_html.exists()
    assert "Docx Test Heading" in out_html.read_text(encoding="utf-8")


def test_pptx_conversion(tmp_path):
    import pptx
    prs = pptx.Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "Presentation Slide Title"
    pptx_file = tmp_path / "sample.pptx"
    prs.save(pptx_file)

    converter = MinerUHTMLConverter()
    out_html = tmp_path / "sample_pptx.html"
    res = converter.convert(pptx_file, output_path=out_html)

    assert res.success is True
    assert out_html.exists()
    assert "Presentation Slide Title" in out_html.read_text(encoding="utf-8")


def test_xlsx_conversion(tmp_path):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws["A1"] = "Metric"
    ws["B1"] = "Score"
    ws["A2"] = "Accuracy"
    ws["B2"] = 99
    xlsx_file = tmp_path / "sample.xlsx"
    wb.save(xlsx_file)

    converter = MinerUHTMLConverter()
    out_html = tmp_path / "sample_xlsx.html"
    res = converter.convert(xlsx_file, output_path=out_html)

    assert res.success is True
    assert out_html.exists()
    assert "Metric" in out_html.read_text(encoding="utf-8")

