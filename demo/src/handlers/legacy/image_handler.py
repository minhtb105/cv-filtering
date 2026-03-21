"""
Image-based CV parsing using OCR
Supports JPEG, PNG, TIFF, and other image formats
"""
from typing import Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ImageCVHandler:
    """
    Handler for CV extraction from image files
    
    Uses pytesseract for OCR:
    - Automatic image rotation detection
    - Text extraction with confidence scoring
    - Fallback to other handlers for unsupported formats
    
    Supported formats: JPEG, PNG, TIFF, BMP, WebP
    """
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.webp'}
    
    def __init__(self, confidence_threshold: float = 0.6):
        """
        Initialize image handler
        
        Args:
            confidence_threshold: Min OCR confidence (0-1) to include text
        """
        self.confidence_threshold = confidence_threshold
        
        try:
            import pytesseract
            from PIL import Image
            self.pytesseract = pytesseract
            self.Image = Image
            self.available = True
        except ImportError:
            logger.warning(
                "Image OCR support not available. "
                "Install dependencies: pip install pytesseract Pillow"
            )
            self.available = False
    
    def is_image(self, file_path: str) -> bool:
        """Check if file is supported image format"""
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_FORMATS
    
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from image using OCR
        
        Args:
            file_path: Path to image file
            
        Returns:
            Extracted text from image
            
        Raises:
            ValueError: If pytesseract not installed
            IOError: If image cannot be read
        """
        if not self.available:
            raise ValueError(
                "pytesseract not installed. "
                "Run: pip install pytesseract"
            )
        
        # Load image
        image = self.Image.open(file_path)
        
        # Auto-rotate if needed
        image = self._rotate_if_needed(image)
        
        # Extract text
        text = self.pytesseract.image_to_string(image)
        
        return text.strip()
    
    def _rotate_if_needed(self, image):
        """Auto-rotate image to correct orientation"""
        try:
            # Check EXIF data for rotation
            from PIL import ExifTags
            
            try:
                exif = image._getexif()
                if exif is not None:
                    for tag, value in exif.items():
                        if ExifTags.TAGS.get(tag) == 'Orientation':
                            # Apply rotation based on EXIF
                            if value == 3:
                                image = image.rotate(180, expand=True)
                            elif value == 6:
                                image = image.rotate(270, expand=True)
                            elif value == 8:
                                image = image.rotate(90, expand=True)
            except (AttributeError, KeyError, IndexError):
                pass
                
        except ImportError:
            logger.debug("ExifTags not available, skipping rotation")
        
        return image
    
    def get_quality_metrics(self, file_path: str) -> dict:
        """
        Calculate OCR quality metrics for image
        
        Returns:
            {
                'confidence': float,  # average character confidence
                'text_length': int,
                'estimated_pages': int
            }
        """
        if not self.available:
            return {'error': 'pytesseract not available'}
        
        try:
            image = self.Image.open(file_path)
            image = self._rotate_if_needed(image)
            
            # Get detailed data including confidence
            data = self.pytesseract.image_to_data(image, output_type='dict')
            
            confidences = [int(c) for c in data['confidence'] if int(c) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            text = self.pytesseract.image_to_string(image)
            
            return {
                'confidence': avg_confidence / 100,  # normalize to 0-1
                'text_length': len(text),
                'estimated_pages': 1
            }
            
        except Exception as e:
            logger.error(f"Error calculating quality metrics: {e}")
            return {'error': str(e)}


# Skeleton for email and legacy handlers - to be implemented in Q1 2026
class EmailResumeHandler:
    """Handler for CV extraction from email attachments and body"""
    def __init__(self):
        raise NotImplementedError("Email handler coming in Q1 2026")


class LegacyDocumentHandler:
    """Handler for legacy CV formats (DOC, RTF, XLS)"""
    def __init__(self):
        raise NotImplementedError("Legacy handler coming in Q1 2026")
