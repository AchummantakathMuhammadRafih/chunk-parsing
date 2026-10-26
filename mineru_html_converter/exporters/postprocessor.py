"""HTML enhancement, base64 asset inlining, themes, and interactive TOC injection."""

import base64
import mimetypes
import re
from pathlib import Path
from typing import List, Tuple
from bs4 import BeautifulSoup

THEME_CSS = {
    "modern": """
/* Modern clean presentation theme */
:root {
  --docvortex-accent: #2563eb;
  --docvortex-accent-hover: #1d4ed8;
  --docvortex-surface: #f8fafc;
  --docvortex-border: #e2e8f0;
  --docvortex-text: #0f172a;
}
body.docvortex-html-body {
  background-color: #f1f5f9;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
.docvortex-document {
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
  border-radius: 12px;
  margin: 2rem auto !important;
  background: #ffffff !important;
  padding: 3.5rem 4rem !important;
}
.docvortex-document table {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.docvortex-figure img {
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
}
""",
    "dark": """
/* Dark mode sleek theme */
:root {
  --docvortex-accent: #60a5fa;
  --docvortex-accent-hover: #93c5fd;
  --docvortex-background: #0f172a;
  --docvortex-surface: #1e293b;
  --docvortex-border: #334155;
  --docvortex-muted: #94a3b8;
  --docvortex-text: #f8fafc;
}
body.docvortex-html-body {
  background-color: #020617;
  color: #f8fafc;
}
.docvortex-document {
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
  border-radius: 12px;
  margin: 2rem auto !important;
  background: #0f172a !important;
  border: 1px solid #1e293b;
  padding: 3.5rem 4rem !important;
}
.docvortex-document th {
  background: #1e293b;
}
.docvortex-document pre, .docvortex-document code {
  background: #1e293b;
  color: #38bdf8;
}
""",
    "readable": """
/* Warm editorial book readability theme */
:root {
  --docvortex-accent: #b45309;
  --docvortex-accent-hover: #92400e;
  --docvortex-background: #fdfbf7;
  --docvortex-surface: #f7f3ec;
  --docvortex-border: #e7dfd5;
  --docvortex-text: #292524;
}
body.docvortex-html-body {
  background-color: #f3efe6;
  font-family: 'Merriweather', Georgia, serif;
}
.docvortex-document {
  border-radius: 6px;
  margin: 2rem auto !important;
  background: #fdfbf7 !important;
  box-shadow: 0 4px 12px rgba(0,0,0,0.04);
  padding: 4rem !important;
  font-size: 17px;
  line-height: 1.8;
}
""",
    "minimal": """
/* Minimal clean styling */
body.docvortex-html-body {
  background-color: #ffffff;
}
.docvortex-document {
  padding: 2rem 2.5rem !important;
}
"""
}

TOC_NAV_STYLE = """
<style id="mineru-toc-style">
.mineru-toc-nav {
  position: fixed;
  top: 2rem;
  right: 2rem;
  width: 260px;
  max-height: calc(100vh - 4rem);
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 10px;
  padding: 1rem 1.25rem;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 0.85rem;
  z-index: 1000;
  transition: all 0.2s ease;
}
.mineru-toc-header {
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 0.75rem;
  color: #64748b;
  margin-bottom: 0.75rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.mineru-toc-list {
  list-style: none;
  padding-left: 0;
  margin: 0;
}
.mineru-toc-item {
  margin-bottom: 0.4rem;
  line-height: 1.4;
}
.mineru-toc-item.level-2 {
  padding-left: 0.75rem;
}
.mineru-toc-item.level-3 {
  padding-left: 1.5rem;
}
.mineru-toc-link {
  color: #334155;
  text-decoration: none;
  transition: color 0.15s;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.mineru-toc-link:hover {
  color: #2563eb;
}
@media screen and (max-width: 1200px) {
  .mineru-toc-nav {
    display: none;
  }
}
</style>
"""


def embed_images_as_base64(html_content: str, asset_paths: List[Path], base_dir: Path) -> Tuple[str, int]:
    """
    Replace relative <img> src tags with inline base64 data URIs.
    
    Args:
        html_content: Raw HTML text.
        asset_paths: List of saved asset paths from conversion.
        base_dir: Directory containing HTML and relative assets.
        
    Returns:
        Tuple of (updated HTML string, embedded image count).
    """
    embedded_count = 0
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Map filenames to resolved absolute paths
    asset_lookup = {p.name: p for p in asset_paths if p.exists()}
    
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src or src.startswith("data:"):
            continue
            
        src_path = Path(src)
        target_file = None
        
        # Check lookup by filename or direct path resolution
        if src_path.name in asset_lookup:
            target_file = asset_lookup[src_path.name]
        else:
            resolved = (base_dir / src).resolve()
            if resolved.exists() and resolved.is_file():
                target_file = resolved
                
        if target_file and target_file.exists():
            mime_type, _ = mimetypes.guess_type(str(target_file))
            if not mime_type:
                mime_type = "image/png" if target_file.suffix.lower() == ".png" else "image/jpeg"
                
            try:
                b64_data = base64.b64encode(target_file.read_bytes()).decode("ascii")
                img["src"] = f"data:{mime_type};base64,{b64_data}"
                embedded_count += 1
            except Exception:
                pass
                
    return str(soup), embedded_count


def inject_theme_and_toc(
    html_content: str,
    theme: str = "modern",
    add_toc: bool = True,
    title: str = "MinerU Document"
) -> str:
    """
    Inject theme styling, meta tags, and interactive Table of Contents into HTML.
    
    Args:
        html_content: Raw or base64-embedded HTML.
        theme: Chosen theme name ('modern', 'dark', 'readable', 'minimal').
        add_toc: Whether to inject floating Table of Contents.
        title: Document title.
        
    Returns:
        Enhanced HTML string.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Ensure title
    if soup.title:
        soup.title.string = title
    elif soup.head:
        new_title = soup.new_tag("title")
        new_title.string = title
        soup.head.append(new_title)
        
    # Inject Theme CSS
    theme_css = THEME_CSS.get(theme.lower(), THEME_CSS["modern"])
    if soup.head:
        style_tag = soup.new_tag("style")
        style_tag["id"] = "mineru-theme-style"
        style_tag.string = theme_css
        soup.head.append(style_tag)
        
    # Build Table of Contents
    if add_toc and soup.body:
        headings = soup.find_all(["h1", "h2", "h3"])
        if len(headings) >= 2:
            toc_items = []
            for idx, h in enumerate(headings):
                # Generate unique ID for anchor navigation
                h_id = h.get("id") or f"heading-{idx}"
                h["id"] = h_id
                
                level = h.name[1]  # '1', '2', or '3'
                h_text = h.get_text().strip()
                if h_text:
                    toc_items.append(f'<li class="mineru-toc-item level-{level}"><a class="mineru-toc-link" href="#{h_id}" title="{h_text}">{h_text}</a></li>')
                    
            if toc_items:
                toc_html = f"""
                <aside class="mineru-toc-nav" id="mineru-toc">
                  <div class="mineru-toc-header">Contents</div>
                  <ul class="mineru-toc-list">
                    {''.join(toc_items)}
                  </ul>
                </aside>
                """
                soup_toc = BeautifulSoup(TOC_NAV_STYLE + toc_html, "html.parser")
                soup.body.insert(0, soup_toc)
                
    return str(soup)
