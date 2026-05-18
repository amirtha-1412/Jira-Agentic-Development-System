"""
vectorstore/repo_loader.py
---------------------------------------------
Repository Loader Module
Dynamically scans and loads source code files
from the project directory into structured
documents ready for ChromaDB embedding.

Supported file types:
  .py, .js, .ts, .jsx, .tsx, .java,
  .go, .rs, .cpp, .c, .h, .md, .txt, .json, .yaml, .yml
"""

import os
import hashlib
from pathlib import Path
from typing import Optional

# ─── Supported source file extensions ───────
SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".go", ".rs", ".cpp", ".c", ".h",
    ".md", ".txt", ".json", ".yaml", ".yml",
    ".html", ".css", ".sql",
}

# ─── Directories to always skip ─────────────
SKIP_DIRS = {
    "venv", ".venv", "__pycache__", ".git",
    "node_modules", ".next", "dist", "build",
    ".pytest_cache", ".mypy_cache", "chroma_db",
    "vectorstore/chroma_db",
}


# ─────────────────────────────────────────────
# Document Model
# ─────────────────────────────────────────────

class RepoDocument:
    """Represents a single loaded source file."""

    def __init__(self, file_path: str, content: str, repo_root: str):
        path          = Path(file_path)
        self.file_path     = file_path
        self.relative_path = str(path.relative_to(repo_root)).replace("\\", "/")
        self.filename      = path.name
        self.extension     = path.suffix.lower()
        self.content       = content
        self.size_bytes    = len(content.encode("utf-8"))
        self.line_count    = content.count("\n") + 1
        self.doc_id        = self._generate_id()

    def _generate_id(self) -> str:
        """Generates a stable unique ID from the relative path."""
        return hashlib.md5(self.relative_path.encode()).hexdigest()

    def to_dict(self) -> dict:
        """Returns a dict representation for ChromaDB metadata."""
        return {
            "doc_id":        self.doc_id,
            "file_path":     self.file_path,
            "relative_path": self.relative_path,
            "filename":      self.filename,
            "extension":     self.extension,
            "size_bytes":    self.size_bytes,
            "line_count":    self.line_count,
        }

    def __repr__(self):
        return f"RepoDocument(path={self.relative_path}, lines={self.line_count})"


# ─────────────────────────────────────────────
# Loader
# ─────────────────────────────────────────────

class RepoLoader:
    """
    Scans a repository directory and loads all
    supported source files as RepoDocument objects.
    """

    def __init__(
        self,
        repo_path: str,
        extensions: Optional[set]  = None,
        skip_dirs: Optional[set]   = None,
        max_file_size_kb: int      = 500,
    ):
        self.repo_path        = os.path.abspath(repo_path)
        self.extensions       = extensions or SUPPORTED_EXTENSIONS
        self.skip_dirs        = skip_dirs  or SKIP_DIRS
        self.max_file_size_kb = max_file_size_kb
        self.documents: list[RepoDocument] = []
        self.errors:    list[dict]         = []

    def load(self) -> list[RepoDocument]:
        """
        Walks the repo directory and loads all matching files.

        Returns:
            list[RepoDocument]: All successfully loaded documents
        """
        self.documents = []
        self.errors    = []

        if not os.path.exists(self.repo_path):
            raise FileNotFoundError(f"Repo path not found: {self.repo_path}")

        for root, dirs, files in os.walk(self.repo_path):
            # Prune skip directories in-place
            dirs[:] = [
                d for d in dirs
                if d not in self.skip_dirs
                and not any(skip in os.path.join(root, d) for skip in self.skip_dirs)
            ]

            for filename in files:
                ext = Path(filename).suffix.lower()
                if ext not in self.extensions:
                    continue

                file_path = os.path.join(root, filename)
                doc = self._load_file(file_path)
                if doc:
                    self.documents.append(doc)

        return self.documents

    def _load_file(self, file_path: str) -> Optional[RepoDocument]:
        """Loads a single file safely, respecting size limits."""
        try:
            # Check file size
            size_kb = os.path.getsize(file_path) / 1024
            if size_kb > self.max_file_size_kb:
                self.errors.append({
                    "file": file_path,
                    "reason": f"File too large ({size_kb:.1f} KB > {self.max_file_size_kb} KB)",
                })
                return None

            # Read with UTF-8, fallback to latin-1
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()

            # Skip empty files
            if not content.strip():
                return None

            return RepoDocument(file_path, content, self.repo_path)

        except PermissionError:
            self.errors.append({"file": file_path, "reason": "Permission denied"})
            return None
        except Exception as e:
            self.errors.append({"file": file_path, "reason": str(e)})
            return None

    def summary(self) -> dict:
        """Returns a summary of the loaded repository."""
        ext_counts: dict = {}
        total_lines = 0
        total_size  = 0

        for doc in self.documents:
            ext_counts[doc.extension] = ext_counts.get(doc.extension, 0) + 1
            total_lines += doc.line_count
            total_size  += doc.size_bytes

        return {
            "repo_path":    self.repo_path,
            "total_files":  len(self.documents),
            "total_lines":  total_lines,
            "total_size_kb": round(total_size / 1024, 2),
            "by_extension": ext_counts,
            "errors":       len(self.errors),
        }


# ─────────────────────────────────────────────
# Quick Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("\n" + "=" * 55)
    print("  REPO LOADER - TEST RUN")
    print("=" * 55)

    # Load current project as the repo
    loader = RepoLoader(repo_path=".")
    docs   = loader.load()
    stats  = loader.summary()

    print(f"\n  [OK] Repo path    : {stats['repo_path']}")
    print(f"  [OK] Total files  : {stats['total_files']}")
    print(f"  [OK] Total lines  : {stats['total_lines']}")
    print(f"  [OK] Total size   : {stats['total_size_kb']} KB")
    print(f"  [OK] Errors       : {stats['errors']}")
    print(f"\n  By extension:")
    for ext, count in sorted(stats["by_extension"].items()):
        print(f"    {ext:<10} : {count} files")

    print(f"\n  Sample documents loaded:")
    for doc in docs[:5]:
        print(f"    [{doc.extension}] {doc.relative_path} ({doc.line_count} lines)")

    print("\n" + "=" * 55)
    print("  [DONE] Repo loader test complete.")
    print("=" * 55 + "\n")
