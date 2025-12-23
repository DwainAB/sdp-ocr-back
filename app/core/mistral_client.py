import base64
import requests
from app.core.config import settings

class MistralOCRClient:
    def __init__(self):
        self.api_key = settings.MISTRAL_API_KEY
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is required")
        self.endpoint = "https://api.mistral.ai/v1/ocr"

    def _encode_to_base64(self, data: bytes) -> str:
        return base64.b64encode(data).decode("utf-8")

    async def process_image_ocr(self, image_bytes: bytes) -> str:
        """
        OCR image using direct API call
        """
        image_base64 = self._encode_to_base64(image_bytes)

        payload = {
            "model": "mistral-ocr-latest",
            "document": {
                "type": "document_url",
                "document_url": f"data:image/png;base64,{image_base64}"
            },
            "include_image_base64": False
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            timeout=120
        )

        if response.status_code != 200:
            raise Exception(f"OCR API error {response.status_code}: {response.text}")

        data = response.json()
        return data.get("text", "")

    async def process_pdf_ocr(self, pdf_bytes: bytes) -> dict:
        """
        OCR PDF using direct API call - returns full response with pages
        """
        pdf_base64 = self._encode_to_base64(pdf_bytes)
        print(f"PDF size: {len(pdf_bytes)} bytes, base64 size: {len(pdf_base64)}")

        payload = {
            "model": "mistral-ocr-latest",
            "document": {
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{pdf_base64}"
            },
            "include_image_base64": False
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            timeout=120
        )

        print(f"Mistral OCR response status: {response.status_code}")

        if response.status_code != 200:
            print(f"OCR API error: {response.text}")
            raise Exception(f"OCR API error {response.status_code}: {response.text}")

        data = response.json()
        print(f"OCR response data: {data}")

        return data

mistral_ocr_client = MistralOCRClient()
