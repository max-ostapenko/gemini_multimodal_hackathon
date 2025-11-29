"""Firebase Cloud Storage utilities."""

import json
import uuid
from datetime import datetime
from typing import Optional

import firebase_admin
from firebase_admin import credentials, storage

from app.config import get_settings


class FirebaseStorage:
    """Service for Firebase Cloud Storage operations."""

    _initialized = False

    def __init__(self):
        """Initialize Firebase app if not already done."""
        if not FirebaseStorage._initialized:
            self._init_firebase()

    def _init_firebase(self):
        """Initialize the Firebase Admin SDK."""
        settings = get_settings()

        try:
            # Try to get existing app
            firebase_admin.get_app()
        except ValueError:
            # Initialize new app
            # Will use GOOGLE_APPLICATION_CREDENTIALS env var if set
            # Otherwise uses default credentials (works in GCP environments)
            try:
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred, {
                    'storageBucket': settings.firebase_storage_bucket
                })
            except Exception:
                # Fallback: initialize without credentials for local testing
                firebase_admin.initialize_app(options={
                    'storageBucket': settings.firebase_storage_bucket
                })

        FirebaseStorage._initialized = True

    def _get_bucket(self):
        """Get the storage bucket."""
        return storage.bucket()

    def upload_html(self, html_content: str, filename: Optional[str] = None) -> str:
        """
        Upload HTML content to Firebase Storage.

        Args:
            html_content: HTML content to upload
            filename: Optional custom filename

        Returns:
            Public URL of the uploaded file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"onepagers/{timestamp}_{unique_id}.html"

        bucket = self._get_bucket()
        blob = bucket.blob(filename)

        blob.upload_from_string(
            html_content,
            content_type="text/html"
        )

        # Make the file publicly accessible
        blob.make_public()

        return blob.public_url

    def upload_json(self, data: dict, filename: Optional[str] = None) -> str:
        """
        Upload JSON data to Firebase Storage.

        Args:
            data: Dictionary to upload as JSON
            filename: Optional custom filename

        Returns:
            Public URL of the uploaded file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"data/{timestamp}_{unique_id}.json"

        bucket = self._get_bucket()
        blob = bucket.blob(filename)

        blob.upload_from_string(
            json.dumps(data, indent=2),
            content_type="application/json"
        )

        blob.make_public()

        return blob.public_url

    def upload_image(
        self,
        image_bytes: bytes,
        filename: Optional[str] = None,
        content_type: str = "image/png"
    ) -> str:
        """
        Upload an image to Firebase Storage.

        Args:
            image_bytes: Image data as bytes
            filename: Optional custom filename
            content_type: MIME type of the image

        Returns:
            Public URL of the uploaded file
        """
        if not filename:
            ext = content_type.split("/")[-1]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"images/{timestamp}_{unique_id}.{ext}"

        bucket = self._get_bucket()
        blob = bucket.blob(filename)

        blob.upload_from_string(image_bytes, content_type=content_type)
        blob.make_public()

        return blob.public_url

    def upload_svg(self, svg_content: str, filename: Optional[str] = None) -> str:
        """
        Upload SVG content to Firebase Storage.

        Args:
            svg_content: SVG content as string
            filename: Optional custom filename

        Returns:
            Public URL of the uploaded file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"diagrams/{timestamp}_{unique_id}.svg"

        bucket = self._get_bucket()
        blob = bucket.blob(filename)

        blob.upload_from_string(
            svg_content,
            content_type="image/svg+xml"
        )

        blob.make_public()

        return blob.public_url
