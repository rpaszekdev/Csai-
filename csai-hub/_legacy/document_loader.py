"""
Document loader for processing PDFs, text files, and markdown files.
Supports optional image extraction from PDFs using PyMuPDF.
"""
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from pypdf import PdfReader

logger = logging.getLogger(__name__)

# Try to import PyMuPDF for image extraction
try:
    import fitz
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    logger.info("PyMuPDF not installed. Image extraction from PDFs will be disabled.")

class Document:
    """Represents a document chunk with metadata."""
    def __init__(self, content: str, metadata: Dict):
        self.content = content
        self.metadata = metadata

    def __repr__(self):
        return f"Document(source={self.metadata.get('source', 'unknown')}, length={len(self.content)})"


class DocumentLoader:
    """Loads and processes various document types."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def load_pdf(self, file_path: Path) -> List[Document]:
        """Load and extract text from PDF files."""
        documents = []
        try:
            reader = PdfReader(str(file_path))
            full_text = ""

            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    full_text += f"\n[Page {page_num + 1}]\n{text}"

            # Chunk the full text
            chunks = self._create_chunks(full_text)
            for i, chunk in enumerate(chunks):
                documents.append(Document(
                    content=chunk,
                    metadata={
                        "source": file_path.name,
                        "type": "pdf",
                        "chunk_id": i,
                        "path": str(file_path)
                    }
                ))

            logger.info(f"Loaded {len(documents)} chunks from PDF: {file_path.name}")
        except Exception as e:
            logger.error(f"Error loading PDF {file_path}: {e}")

        return documents

    def load_text(self, file_path: Path) -> List[Document]:
        """Load text or markdown files."""
        documents = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Chunk the content
            chunks = self._create_chunks(content)
            for i, chunk in enumerate(chunks):
                documents.append(Document(
                    content=chunk,
                    metadata={
                        "source": file_path.name,
                        "type": "txt" if file_path.suffix == ".txt" else "markdown",
                        "chunk_id": i,
                        "path": str(file_path)
                    }
                ))

            logger.info(f"Loaded {len(documents)} chunks from text file: {file_path.name}")
        except Exception as e:
            logger.error(f"Error loading text file {file_path}: {e}")

        return documents

    def load_from_paths(self, paths: List[Path]) -> List[Document]:
        """Load documents from a list of file or directory paths."""
        all_documents = []

        for path in paths:
            if not path.exists():
                logger.warning(f"Path does not exist: {path}")
                continue

            if path.is_file():
                # Single file
                docs = self._load_single_file(path)
                all_documents.extend(docs)
            elif path.is_dir():
                # Directory - load all supported files
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        docs = self._load_single_file(file_path)
                        all_documents.extend(docs)

        logger.info(f"Total documents loaded: {len(all_documents)}")
        return all_documents

    def _load_single_file(self, file_path: Path) -> List[Document]:
        """Load a single file based on its extension."""
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return self.load_pdf(file_path)
        elif suffix in [".txt", ".md"]:
            return self.load_text(file_path)
        else:
            logger.debug(f"Skipping unsupported file type: {file_path}")
            return []

    def _create_chunks(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        if not text:
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.chunk_size
            chunk = text[start:end]

            # Try to break at sentence or paragraph boundaries
            if end < text_length:
                # Look for the last sentence boundary in the chunk
                for delimiter in ['\n\n', '\n', '. ', '! ', '? ']:
                    last_delim = chunk.rfind(delimiter)
                    if last_delim > self.chunk_size * 0.5:  # At least 50% of chunk size
                        chunk = chunk[:last_delim + len(delimiter)]
                        break

            chunks.append(chunk.strip())
            start += self.chunk_size - self.chunk_overlap

        return [c for c in chunks if c]  # Filter empty chunks

    def extract_images_from_pdf(self, file_path: Path,
                                 output_dir: Optional[Path] = None,
                                 min_width: int = 100,
                                 min_height: int = 100) -> List[Dict]:
        """
        Extract images from a PDF file using PyMuPDF.

        Args:
            file_path: Path to the PDF file
            output_dir: Directory to save extracted images (default: same as PDF)
            min_width: Minimum image width to extract (filters icons/bullets)
            min_height: Minimum image height to extract

        Returns:
            List of dicts with image info: {path, page, width, height, index}
        """
        if not HAS_PYMUPDF:
            logger.warning("PyMuPDF not installed. Cannot extract images.")
            return []

        if output_dir is None:
            output_dir = file_path.parent / f"{file_path.stem}_images"

        output_dir.mkdir(parents=True, exist_ok=True)
        extracted_images = []

        try:
            doc = fitz.open(str(file_path))

            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()

                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        width = base_image["width"]
                        height = base_image["height"]

                        # Filter small images
                        if width < min_width or height < min_height:
                            continue

                        # Save image
                        image_filename = f"page{page_num + 1}_img{img_index}.{image_ext}"
                        image_path = output_dir / image_filename

                        with open(image_path, "wb") as img_file:
                            img_file.write(image_bytes)

                        extracted_images.append({
                            "path": str(image_path),
                            "page": page_num + 1,
                            "width": width,
                            "height": height,
                            "index": img_index,
                            "source_pdf": str(file_path)
                        })

                        logger.debug(f"Extracted image: {image_filename} ({width}x{height})")

                    except Exception as e:
                        logger.debug(f"Could not extract image {img_index} from page {page_num}: {e}")

            doc.close()
            logger.info(f"Extracted {len(extracted_images)} images from {file_path.name}")

        except Exception as e:
            logger.error(f"Error extracting images from PDF {file_path}: {e}")

        return extracted_images

    def get_pdf_page_count(self, file_path: Path) -> int:
        """Get the number of pages in a PDF file."""
        try:
            reader = PdfReader(str(file_path))
            return len(reader.pages)
        except Exception as e:
            logger.error(f"Error getting page count for {file_path}: {e}")
            return 0
