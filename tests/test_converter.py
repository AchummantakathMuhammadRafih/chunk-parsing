"""Unit and integration tests for MinerU PDF Converter."""

import base64
import os
import tempfile
import unittest
from pathlib import Path
from click.testing import CliRunner

from mineru_converter.config.constants import BackendType, ParseMethod
from mineru_converter.config.settings import ConversionConfig
from mineru_converter.core.docling_client import DoclingClient, DoclingClientError
from mineru_converter.core.validator import validate_pdf_document, PDFValidationError
from mineru_converter.exporters.docling_chunks import attach_images_to_chunks, build_image_label
from mineru_converter.exporters.manifest import (
    build_output_manifest,
    calculate_document_stats,
)
from mineru_converter.utils.file_utils import (
    compute_file_sha256,
    find_input_files,
    format_file_size,
    sanitize_filename,
)
from mineru_converter.cli.app import cli
from mineru_converter.utils.logging_utils import get_logger


class TestMinerUConverter(unittest.TestCase):

    def test_conversion_config_defaults(self):
        config = ConversionConfig()
        self.assertEqual(config.backend, BackendType.PIPELINE)
        self.assertEqual(config.method, ParseMethod.AUTO)
        self.assertEqual(config.lang, "ch")
        self.assertTrue(config.formula_enable)
        self.assertTrue(config.table_enable)
        self.assertTrue(config.dump_md)
        self.assertTrue(config.dump_content_list)
        self.assertTrue(config.dump_middle_json)
        self.assertTrue(config.draw_layout_bbox)
        self.assertTrue(config.draw_span_bbox)
        self.assertEqual(config.docling_max_tokens, 1024)
        self.assertEqual(config.docling_tokenizer, "BAAI/bge-m3")

    def test_language_normalization(self):
        cfg1 = ConversionConfig(lang="en")
        self.assertEqual(cfg1.lang, "ch")
        cfg2 = ConversionConfig(lang="english")
        self.assertEqual(cfg2.lang, "ch")
        cfg3 = ConversionConfig(lang="korean")
        self.assertEqual(cfg3.lang, "korean")

    def test_file_utilities(self):
        self.assertEqual(format_file_size(500), "500 B")
        self.assertEqual(format_file_size(1024), "1.00 KB")
        self.assertEqual(format_file_size(1024 * 1024 * 3), "3.00 MB")
        self.assertEqual(sanitize_filename('sample:file/name*?'), "sample_file_name")

    def test_pdf_validation_real_pdf(self):
        pdf_path = Path("input/UsabilityTestingOfMedicalDevices_2014-Ch12.pdf")
        if pdf_path.exists():
            total, start, end = validate_pdf_document(pdf_path, start_page=0, end_page=2)
            self.assertEqual(total, 40)
            self.assertEqual(start, 0)
            self.assertEqual(end, 2)

    def test_pdf_validation_missing_file(self):
        with self.assertRaises(PDFValidationError):
            validate_pdf_document(Path("non_existent_file.pdf"))

    def test_pdf_validation_invalid_bounds(self):
        pdf_path = Path("input/UsabilityTestingOfMedicalDevices_2014-Ch12.pdf")
        if pdf_path.exists():
            with self.assertRaises(PDFValidationError):
                validate_pdf_document(pdf_path, start_page=100)
            with self.assertRaises(PDFValidationError):
                validate_pdf_document(pdf_path, start_page=5, end_page=2)

    def test_manifest_builder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            doc_stem = "sample_doc"
            
            # Create dummy artifacts
            (tmp_path / f"{doc_stem}.md").write_text("# Title\nSample text", encoding="utf-8")
            (tmp_path / f"{doc_stem}_content_list.json").write_text("[]", encoding="utf-8")
            (tmp_path / f"{doc_stem}_content_list_v2.json").write_text("[]", encoding="utf-8")
            (tmp_path / f"{doc_stem}_middle.json").write_text('{"pdf_info": []}', encoding="utf-8")
            (tmp_path / f"{doc_stem}_model.json").write_text("{}", encoding="utf-8")
            
            manifest = build_output_manifest(tmp_path, doc_stem)
            self.assertEqual(manifest.markdown_path, tmp_path / f"{doc_stem}.md")
            self.assertEqual(manifest.content_list_v1_path, tmp_path / f"{doc_stem}_content_list.json")
            self.assertEqual(manifest.content_list_v2_path, tmp_path / f"{doc_stem}_content_list_v2.json")
            self.assertEqual(manifest.middle_json_path, tmp_path / f"{doc_stem}_middle.json")
            self.assertEqual(manifest.model_json_path, tmp_path / f"{doc_stem}_model.json")

    def test_cli_info_command(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["info"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("MinerU", result.output)

    def test_cli_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("convert", result.output)
        self.assertIn("batch", result.output)
        self.assertIn("inspect", result.output)
        self.assertIn("info", result.output)


class TestDoclingChunks(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        (self.base / "images").mkdir()
        for name in ("a.jpg", "b.jpg", "c.jpg", "d.jpg"):
            (self.base / "images" / name).write_bytes(name.encode())

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def _img(path, caption=None, footnote=None):
        return {"type": "image", "img_path": f"images/{path}",
                "image_caption": caption or [], "image_footnote": footnote or []}

    def test_build_image_label(self):
        self.assertEqual(build_image_label(["Cap 1", "Cap 2"], []), "Cap 1, Cap 2")
        self.assertEqual(build_image_label([], ["Fn"]), "Fn")
        self.assertEqual(build_image_label(["Cap"], ["F1", "F2"]), "Cap. F1, F2")
        self.assertEqual(build_image_label(["a [b]\nc"], []), "a (b) c")
        self.assertEqual(build_image_label([], []), "")

    def test_attach_keeps_all_images_in_order(self):
        images = [
            self._img("a.jpg", caption=["Figure 1"]),
            self._img("b.jpg"),
            self._img("c.jpg", footnote=["Note"]),
            self._img("d.jpg", caption=["Figure 2"], footnote=["Src"]),
        ]
        chunks = [
            {"chunk_index": 0, "text": "Intro\n![IMAGE]", "doc_items": ["#/pictures/0"]},
            {"chunk_index": 1, "text": "move\n![IMAGE]\nforward\n![IMAGE]\n![IMAGE]",
             "doc_items": ["#/pictures/1", "#/pictures/2", "#/pictures/3"]},
        ]
        attached = attach_images_to_chunks(chunks, images, self.base)

        self.assertEqual(attached, 4)
        b64 = lambda n: base64.b64encode(n.encode()).decode()
        self.assertEqual(chunks[0]["text"], "Intro\n![Figure 1]")
        self.assertEqual(chunks[0]["images"], [b64("a.jpg")])
        self.assertEqual(chunks[1]["text"], "move\n![IMAGE]\nforward\n![Note]\n![Figure 2. Src]")
        self.assertEqual(chunks[1]["images"], [b64("b.jpg"), b64("c.jpg"), b64("d.jpg")])
        for c in chunks:
            self.assertEqual(len(c["images"]), c["text"].count("!["))
            self.assertTrue(all(isinstance(i, str) for i in c["images"]))

    def test_chunk_without_images_gets_empty_list(self):
        chunks = [{"chunk_index": 0, "text": "plain"}]
        attach_images_to_chunks(chunks, [], self.base)
        self.assertEqual(chunks[0]["images"], [])
        self.assertEqual(chunks[0]["text"], "plain")

    def test_mismatch_logs_warning(self):
        chunks = [{"chunk_index": 0, "text": "x\n![IMAGE]"}]
        with self.assertLogs(get_logger(), level="WARNING") as logs:
            attach_images_to_chunks(chunks, [], self.base)
        self.assertTrue(any("misaligned" in m for m in logs.output))
        self.assertEqual(chunks[0]["text"], "x\n![IMAGE]")
        self.assertEqual(chunks[0]["images"], [""])

    def test_path_traversal_is_not_read(self):
        chunks = [{"chunk_index": 0, "text": "![IMAGE]"}]
        images = [{"type": "image", "img_path": "../outside.jpg", "image_caption": ["c"]}]
        attach_images_to_chunks(chunks, images, self.base)
        self.assertEqual(chunks[0]["images"], [""])
        self.assertEqual(chunks[0]["text"], "![c]")

    def test_unreachable_server_raises_client_error(self):
        client = DoclingClient(server_url="http://127.0.0.1:1", timeout=2)
        with self.assertRaises(DoclingClientError):
            client.chunk_markdown("# hi")


if __name__ == "__main__":
    unittest.main()
