import io
from typing import List
import PyPDF2

class PDFSplitter:
    """
    PDF splitter using PyPDF2 - pure Python, compatible with all platforms
    """

    def split_pdf_to_pages(self, pdf_bytes: bytes, max_pages: int = None) -> List[bytes]:
        """
        Split PDF into individual page PDFs using PyPDF2

        Args:
            pdf_bytes: PDF content as bytes
            max_pages: Maximum pages to process (None = all pages)

        Returns:
            List of PDF pages as bytes
        """
        try:
            # Open PDF from bytes
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
            total_pages = len(pdf_reader.pages)

            if total_pages == 0:
                raise Exception("PDF has no pages")

            pages_to_process = total_pages if max_pages is None else min(max_pages, total_pages)
            print(f"PDF has {total_pages} pages, processing {pages_to_process} page(s)")

            page_pdfs = []

            for page_num in range(pages_to_process):
                print(f"Splitting page {page_num + 1}")

                # Create new PDF with single page
                pdf_writer = PyPDF2.PdfWriter()
                pdf_writer.add_page(pdf_reader.pages[page_num])

                # Convert to bytes
                output_buffer = io.BytesIO()
                pdf_writer.write(output_buffer)
                page_pdf_bytes = output_buffer.getvalue()

                page_pdfs.append(page_pdf_bytes)
                output_buffer.close()

            return page_pdfs

        except Exception as e:
            print(f"PDF splitting failed: {e}")
            raise Exception(f"Cannot split PDF: {e}")

pdf_splitter = PDFSplitter()