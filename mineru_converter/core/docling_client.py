"""Minimal HTTP client for docling-serve chunking endpoints."""

import base64
import json
import socket
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from mineru_converter.config.constants import DEFAULT_DOCLING_URL, DOCLING_HYBRID_CHUNK_ENDPOINT


class DoclingClientError(RuntimeError):
    """Raised when docling-serve is unreachable or returns an error."""


class DoclingClient:
    """Client for the docling-serve hybrid chunking API."""

    def __init__(
        self,
        server_url: str = DEFAULT_DOCLING_URL,
        timeout: int = 300,
        max_tokens: Optional[int] = None,
        tokenizer: Optional[str] = None,
    ):
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.tokenizer = tokenizer

    def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = Request(
            f"{self.server_url}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise DoclingClientError(f"docling-serve HTTP {exc.code} on {path}: {detail}") from exc
        except (URLError, socket.timeout, TimeoutError) as exc:
            raise DoclingClientError(f"Cannot reach docling-serve at {self.server_url}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise DoclingClientError(f"Invalid JSON from docling-serve on {path}: {exc}") from exc

    def health_check(self) -> bool:
        try:
            return self._request("GET", "/health").get("status") == "ok"
        except DoclingClientError:
            return False

    def chunk_markdown(self, markdown_text: str, filename: str = "document.md") -> List[Dict[str, Any]]:
        """Chunk Markdown with the hybrid chunker and return docling's chunk list."""
        chunking_options: Dict[str, Any] = {
            "chunker": "hybrid",
            "use_markdown_images": True,
            "include_raw_text": True,
            "merge_peers": True,
        }
        if self.tokenizer:
            chunking_options["tokenizer"] = self.tokenizer
        if self.max_tokens:
            chunking_options["max_tokens"] = self.max_tokens

        payload = {
            "sources": [{
                "kind": "file",
                "base64_string": base64.b64encode(markdown_text.encode("utf-8")).decode("ascii"),
                "filename": filename,
            }],
            "chunking_options": chunking_options,
        }
        response = self._request("POST", DOCLING_HYBRID_CHUNK_ENDPOINT, payload)
        chunks = response.get("chunks") if isinstance(response, dict) else None
        if chunks is None:
            raise DoclingClientError(f"Unexpected docling-serve response keys: {list(response)[:10]}")
        return chunks
