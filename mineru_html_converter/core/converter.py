"""Core MinerU PDF to HTML conversion engine."""

import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

import docvortex
from docvortex.render import HtmlRenderOptions, RenderFormat, RenderMode

from mineru_html_converter.config.constants import RenderModeEnum
from mineru_html_converter.config.settings import HTMLConversionConfig
from mineru_html_converter.exporters.postprocessor import (
    embed_images_as_base64,
    inject_theme_and_toc,
)
from mineru_html_converter.models.schemas import HTMLConversionResult
from mineru_html_converter.utils.file_utils import ensure_directory, sanitize_filename
from mineru_html_converter.utils.logging_utils import logger


class MinerUHTMLConverter:
    """
    High-level orchestrator for converting PDF documents into semantic, responsive HTML
    using the MinerU document layout engine.
    """

    def __init__(self, config: Optional[HTMLConversionConfig] = None):
        """Initialize the converter with configuration."""
        self.config = config or HTMLConversionConfig()

    def convert(
        self,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        override_config: Optional[HTMLConversionConfig] = None,
    ) -> HTMLConversionResult:
        """
        Convert a PDF file to an HTML document.

        Args:
            input_path: Path to the target PDF.
            output_path: Optional explicit output HTML path. Defaults to output_dir / <stem>.html.
            override_config: Optional configuration overrides.

        Returns:
            HTMLConversionResult containing status, output path, metrics, and duration.
        """
        cfg = override_config or self.config
        pdf_file = Path(input_path).resolve()
        start_time = time.time()
        start_dt = datetime.utcnow()

        if not pdf_file.exists():
            error_msg = f"Input file not found: {pdf_file}"
            logger.error(f"[bold red]{error_msg}[/bold red]")
            return HTMLConversionResult(
                success=False,
                input_file=pdf_file,
                output_html_file=Path(""),
                document_name=pdf_file.stem,
                error_message=error_msg,
                duration_seconds=0.0,
                converted_at=start_dt,
            )

        doc_stem = sanitize_filename(pdf_file.stem)
        target_dir = ensure_directory(cfg.output_dir)

        if output_path is not None:
            final_html_path = Path(output_path).resolve()
            ensure_directory(final_html_path.parent)
        else:
            final_html_path = target_dir / f"{doc_stem}.html"

        logger.info(f"Converting [bold cyan]{pdf_file.name}[/bold cyan] -> [bold green]{final_html_path.name}[/bold green]")
        logger.debug(f"Config: mode={cfg.mode}, embed_images={cfg.embed_images}, theme={cfg.theme}")

        try:
            # 1. Map RenderMode
            render_mode = RenderMode.FULL if cfg.mode == RenderModeEnum.FULL else RenderMode.DEFAULT
            title = cfg.document_title or doc_stem.replace("_", " ").title()

            html_opts = HtmlRenderOptions(
                mode=render_mode,
                standalone=cfg.standalone,
                document_title=title,
            )

            # 2. Execute MinerU core conversion via docvortex
            page_range_str = cfg.pages or ""
            export_result = docvortex.convert(
                source=pdf_file,
                output_path=final_html_path,
                output_format=RenderFormat.HTML,
                page_range=page_range_str,
                options=html_opts,
                overwrite=cfg.overwrite,
            )

            # 3. Read generated HTML
            if not final_html_path.exists():
                raise RuntimeError("HTML output file was not created by the conversion pipeline.")

            html_text = final_html_path.read_text(encoding="utf-8")

            # 4. Optional Base64 Image Inlining
            embedded_count = 0
            asset_paths = list(export_result.asset_paths) if export_result.asset_paths else []
            if cfg.embed_images and asset_paths:
                logger.debug(f"Embedding {len(asset_paths)} image assets into HTML as base64...")
                html_text, embedded_count = embed_images_as_base64(
                    html_content=html_text,
                    asset_paths=asset_paths,
                    base_dir=final_html_path.parent,
                )

            # 5. Inject Theme & interactive TOC
            html_text = inject_theme_and_toc(
                html_content=html_text,
                theme=cfg.theme.value,
                add_toc=cfg.add_toc,
                title=title,
            )

            # 6. Write final enhanced HTML file
            final_html_path.write_text(html_text, encoding="utf-8")
            file_size = final_html_path.stat().st_size
            duration = round(time.time() - start_time, 2)

            logger.info(
                f"[bold green]Converted successfully:[/bold green] {final_html_path.name} "
                f"({file_size:,} bytes, {embedded_count} images embedded, {duration}s)"
            )

            return HTMLConversionResult(
                success=True,
                input_file=pdf_file,
                output_html_file=final_html_path,
                document_name=doc_stem,
                asset_paths=asset_paths,
                embedded_images_count=embedded_count,
                file_size_bytes=file_size,
                duration_seconds=duration,
                converted_at=start_dt,
            )

        except Exception as exc:
            duration = round(time.time() - start_time, 2)
            logger.error(f"[bold red]Conversion failed for {pdf_file.name}:[/bold red] {exc}", exc_info=True)
            return HTMLConversionResult(
                success=False,
                input_file=pdf_file,
                output_html_file=final_html_path,
                document_name=doc_stem,
                error_message=str(exc),
                duration_seconds=duration,
                converted_at=start_dt,
            )
