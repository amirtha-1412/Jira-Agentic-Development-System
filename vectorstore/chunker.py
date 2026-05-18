"""
vectorstore/chunker.py
---------------------------------------------
Code Chunker Module
Splits large source files into smaller,
semantically meaningful chunks for efficient
LLM embedding and retrieval.

Chunking strategy:
  - Python: split by function/class definitions
  - Other:  split by fixed line windows with overlap
"""

import re
from vectorstore.repo_loader import RepoDocument


# ─────────────────────────────────────────────
# Chunk Model
# ─────────────────────────────────────────────

class CodeChunk:
    """Represents a single chunk of code from a source file."""

    def __init__(
        self,
        content:       str,
        source_doc:    RepoDocument,
        chunk_index:   int,
        start_line:    int,
        end_line:      int,
        chunk_type:    str = "window",
    ):
        self.content     = content.strip()
        self.source_path = source_doc.relative_path
        self.extension   = source_doc.extension
        self.filename    = source_doc.filename
        self.doc_id      = source_doc.doc_id
        self.chunk_index = chunk_index
        self.start_line  = start_line
        self.end_line    = end_line
        self.chunk_type  = chunk_type          # "function", "class", "window"
        self.chunk_id    = f"{source_doc.doc_id}_chunk_{chunk_index}"
        self.line_count  = end_line - start_line + 1

    def to_metadata(self) -> dict:
        """Returns ChromaDB-compatible metadata dict."""
        return {
            "chunk_id":    self.chunk_id,
            "doc_id":      self.doc_id,
            "source_path": self.source_path,
            "filename":    self.filename,
            "extension":   self.extension,
            "chunk_index": self.chunk_index,
            "start_line":  self.start_line,
            "end_line":    self.end_line,
            "chunk_type":  self.chunk_type,
            "line_count":  self.line_count,
        }

    def __repr__(self):
        return (
            f"CodeChunk(src={self.source_path}, "
            f"idx={self.chunk_index}, "
            f"lines={self.start_line}-{self.end_line}, "
            f"type={self.chunk_type})"
        )


# ─────────────────────────────────────────────
# Chunker
# ─────────────────────────────────────────────

class CodeChunker:
    """
    Splits RepoDocument objects into CodeChunk objects.

    Strategies:
      - Python (.py): semantic split by def/class blocks
      - All others:   sliding window with overlap
    """

    def __init__(
        self,
        window_size: int  = 50,    # lines per chunk (non-Python)
        overlap:     int  = 10,    # overlap lines between chunks
        min_lines:   int  = 3,     # skip chunks shorter than this
    ):
        self.window_size = window_size
        self.overlap     = overlap
        self.min_lines   = min_lines

    def chunk(self, doc: RepoDocument) -> list[CodeChunk]:
        """
        Chunks a single RepoDocument.

        Args:
            doc: RepoDocument to chunk

        Returns:
            list[CodeChunk]: List of non-empty chunks
        """
        if doc.extension == ".py":
            return self._chunk_python(doc)
        else:
            return self._chunk_window(doc)

    def chunk_all(self, docs: list[RepoDocument]) -> list[CodeChunk]:
        """
        Chunks all documents in a list.

        Returns:
            list[CodeChunk]: All chunks from all documents
        """
        all_chunks = []
        for doc in docs:
            chunks = self.chunk(doc)
            all_chunks.extend(chunks)
        return all_chunks

    # ─────────────────────────────────────────
    # Python Semantic Chunker
    # ─────────────────────────────────────────

    def _chunk_python(self, doc: RepoDocument) -> list[CodeChunk]:
        """
        Splits Python files by top-level def/class blocks.
        Falls back to window chunking for non-structured files.
        """
        lines       = doc.content.splitlines()
        chunks      = []
        chunk_index = 0
        block_start = None
        block_lines = []

        # Regex: top-level def or class (no leading whitespace)
        block_pattern = re.compile(r"^(def |class )")

        for i, line in enumerate(lines):
            line_no = i + 1

            if block_pattern.match(line):
                # Save previous block if exists
                if block_lines and len(block_lines) >= self.min_lines:
                    chunks.append(self._make_chunk(
                        block_lines, doc, chunk_index,
                        block_start, block_start + len(block_lines) - 1,
                        "function"
                    ))
                    chunk_index += 1

                # Start new block
                block_start = line_no
                block_lines = [line]
            else:
                if block_start is not None:
                    block_lines.append(line)

        # Save last block
        if block_lines and len(block_lines) >= self.min_lines:
            chunks.append(self._make_chunk(
                block_lines, doc, chunk_index,
                block_start, block_start + len(block_lines) - 1,
                "function"
            ))

        # Fallback: if no blocks found, use window
        if not chunks:
            return self._chunk_window(doc)

        return chunks

    # ─────────────────────────────────────────
    # Sliding Window Chunker
    # ─────────────────────────────────────────

    def _chunk_window(self, doc: RepoDocument) -> list[CodeChunk]:
        """
        Splits any file into fixed-size windows with overlap.
        """
        lines       = doc.content.splitlines()
        chunks      = []
        chunk_index = 0
        step        = max(1, self.window_size - self.overlap)
        i           = 0

        while i < len(lines):
            window     = lines[i : i + self.window_size]
            start_line = i + 1
            end_line   = i + len(window)

            if len(window) >= self.min_lines:
                chunks.append(self._make_chunk(
                    window, doc, chunk_index,
                    start_line, end_line, "window"
                ))
                chunk_index += 1

            i += step

        return chunks

    # ─────────────────────────────────────────
    # Helper
    # ─────────────────────────────────────────

    def _make_chunk(
        self,
        lines:       list,
        doc:         RepoDocument,
        chunk_index: int,
        start_line:  int,
        end_line:    int,
        chunk_type:  str,
    ) -> CodeChunk:
        content = "\n".join(lines)
        return CodeChunk(
            content    = content,
            source_doc = doc,
            chunk_index= chunk_index,
            start_line = start_line,
            end_line   = end_line,
            chunk_type = chunk_type,
        )


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    from vectorstore.repo_loader import RepoLoader

    print("\n" + "=" * 55)
    print("  CHUNKER - TEST RUN")
    print("=" * 55)

    # Load project files
    loader  = RepoLoader(repo_path=".")
    docs    = loader.load()
    chunker = CodeChunker(window_size=50, overlap=10)
    chunks  = chunker.chunk_all(docs)

    # Summary
    py_chunks    = [c for c in chunks if c.extension == ".py"]
    other_chunks = [c for c in chunks if c.extension != ".py"]
    func_chunks  = [c for c in chunks if c.chunk_type == "function"]
    win_chunks   = [c for c in chunks if c.chunk_type == "window"]

    print(f"\n  [OK] Documents loaded  : {len(docs)}")
    print(f"  [OK] Total chunks      : {len(chunks)}")
    print(f"  [OK] Python chunks     : {len(py_chunks)}")
    print(f"  [OK] Other chunks      : {len(other_chunks)}")
    print(f"  [OK] Function chunks   : {len(func_chunks)}")
    print(f"  [OK] Window chunks     : {len(win_chunks)}")

    print(f"\n  Sample chunks:")
    for c in chunks[:5]:
        print(f"    [{c.chunk_type}] {c.source_path} "
              f"lines {c.start_line}-{c.end_line} "
              f"({c.line_count} lines)")

    print(f"\n  Sample chunk content preview:")
    if chunks:
        sample = chunks[0]
        print(f"  File   : {sample.source_path}")
        print(f"  Lines  : {sample.start_line}-{sample.end_line}")
        print(f"  Type   : {sample.chunk_type}")
        preview = sample.content[:200].replace("\n", " | ")
        print(f"  Content: {preview}...")

    print("\n" + "=" * 55)
    print("  [DONE] Chunker test complete.")
    print("=" * 55 + "\n")
