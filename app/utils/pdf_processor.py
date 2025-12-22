import io
import fitz  # PyMuPDF
from pdf2image import convert_from_bytes
from typing import List
from PIL import Image

class PDFProcessor:
    def __init__(self):
        pass

    def split_pdf_to_pages(self, pdf_bytes: bytes, max_pages: int = None) -> List[bytes]:
        """
        Split PDF into individual page PDFs (limit to first page for testing)
        """
        pdf_doc = None
        try:
            pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            if pdf_doc.page_count == 0:
                raise Exception("PDF has no pages")

            total_pages = pdf_doc.page_count
            pages_to_process = total_pages if max_pages is None else min(max_pages, total_pages)

            print(f"PDF has {total_pages} pages, processing {pages_to_process} page(s)")

            page_pdfs = []

            for page_num in range(pages_to_process):
                print(f"Processing page {page_num + 1}")
                # Create new PDF with single page
                new_doc = fitz.open()
                new_doc.insert_pdf(pdf_doc, from_page=page_num, to_page=page_num)

                # Convert to bytes
                page_pdf_bytes = new_doc.tobytes()
                page_pdfs.append(page_pdf_bytes)
                new_doc.close()

            return page_pdfs

        except Exception as pymupdf_error:
            # If PDF splitting fails, raise error
            print(f"PDF splitting failed: {pymupdf_error}")
            raise Exception(f"Cannot split PDF: {pymupdf_error}")

        finally:
            if pdf_doc:
                pdf_doc.close()

    def split_pdf_to_page_pdfs(self, pdf_bytes: bytes) -> List[bytes]:
        """
        Split PDF into individual PDF pages - PDF format only
        """
        # Validate PDF size
        if len(pdf_bytes) < 100:
            raise Exception("PDF file is too small or empty")

        # Try to split PDF into individual pages
        return self.split_pdf_to_pages(pdf_bytes)

    def _convert_with_pymupdf(self, pdf_bytes: bytes) -> List[bytes]:
        """Convert using PyMuPDF"""
        pdf_doc = None
        try:
            pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            if pdf_doc.page_count == 0:
                raise Exception("PDF has no pages")

            image_bytes_list = []
            for page_num in range(pdf_doc.page_count):
                page = pdf_doc[page_num]
                # Reduce DPI to avoid memory issues
                mat = fitz.Matrix(1.5, 1.5)  # 1.5 = ~225dpi
                pix = page.get_pixmap(matrix=mat)

                img_byte_arr = io.BytesIO()
                img_byte_arr.write(pix.tobytes("jpeg"))
                img_byte_arr.seek(0)
                image_bytes_list.append(img_byte_arr.getvalue())

            return image_bytes_list

        finally:
            if pdf_doc:
                pdf_doc.close()

    def _convert_with_pdf2image(self, pdf_bytes: bytes) -> List[bytes]:
        """Convert using pdf2image (requires poppler)"""
        # Convert PDF to images with reduced DPI - LIMIT TO 10 PAGES MAX
        images = convert_from_bytes(pdf_bytes, dpi=200, fmt='jpeg', last_page=10)

        image_bytes_list = []
        for image in images:
            # Compress image to reduce size
            img_byte_arr = io.BytesIO()

            # Resize if too large
            if image.width > 2000:
                ratio = 2000 / image.width
                new_height = int(image.height * ratio)
                image = image.resize((2000, new_height), Image.Resampling.LANCZOS)

            image.save(img_byte_arr, format='JPEG', quality=85, optimize=True)
            img_byte_arr.seek(0)
            image_bytes_list.append(img_byte_arr.getvalue())

        return image_bytes_list

pdf_processor = PDFProcessor()