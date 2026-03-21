# 📋 ADD_NEW_FORMAT.md - Adding Support for New Document Types

**Date**: March 20, 2026  
**Purpose**: Guide for extending CV Intelligence to support additional file formats  
**Target Audience**: Developers, DevOps engineers  

---

## 🎯 Overview

The CV Intelligence Platform uses a **plugin-based architecture** to support multiple document formats. This guide walks you through adding support for new file types (e.g., PNG, JPG, DOC) to the system.

### Current Supported Formats
- ✅ PDF (.pdf)
- ✅ DOCX (.docx)
- ⏳ Image OCR (.png, .jpg) - Stub

### Architecture
```
[User File] 
    ↓
InputHandlerFactory
    ↓
    ├─ PDFHandler → Text
    ├─ DOCXHandler → Text
    └─ NewHandler → Text
    ↓
CVExtractor (spaCy NER)
    ↓
Structured Data
```

---

## 📝 Step-By-Step Guide

### Step 1: Create Handler Class

Create a new handler file for your format:

**File**: `demo/src/handlers/input_handlers.py`

```python
from abc import ABC, abstractmethod
from pathlib import Path


class ImageOCRHandler(ABC):
    """Handler for image-based CV files (PNG, JPG)"""
    
    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """
        Extract text from image using OCR
        
        Args:
            file_path: Path to image file
            
        Returns:
            Extracted text
            
        Raises:
            ImportError: If required OCR library not installed
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Requires pytesseract and Tesseract-OCR installed
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            raise ImportError(
                "OCR support requires: pip install pytesseract pillow\n"
                "Also install Tesseract-OCR: https://github.com/UB-Mannheim/tesseract/wiki"
            )
        
        # Load image
        image = Image.open(file_path)
        
        # Extract text
        text = pytesseract.image_to_string(image)
        
        return text
    
    @classmethod
    def validate(cls, file_path: str) -> bool:
        """Check if file is a valid image"""
        path = Path(file_path)
        return path.suffix.lower() in ['.png', '.jpg', '.jpeg']
    
    @classmethod
    @property
    def supported_formats(cls):
        return ['.png', '.jpg', '.jpeg']
```

### Step 2: Register Handler

Add handler to the factory in the same file:

```python
class InputHandlerFactory:
    """Factory for creating input handlers"""
    
    _handlers = {
        '.pdf': PDFHandler,
        '.docx': DOCXHandler,
        '.png': ImageOCRHandler,
        '.jpg': ImageOCRHandler,
        '.jpeg': ImageOCRHandler,
    }
    
    @classmethod
    def get_handler(cls, file_path: str):
        """Get appropriate handler for file"""
        ext = Path(file_path).suffix.lower()
        
        handler = cls._handlers.get(ext)
        if not handler:
            raise ValueError(f"Unsupported format: {ext}")
        
        return handler
    
    @classmethod
    def register_handler(cls, extensions: List[str], handler):
        """Register new handler for extensions"""
        for ext in extensions:
            cls._handlers[ext] = handler
```

### Step 3: Install Dependencies

If your handler requires external libraries:

```bash
# For OCR support
pip install pytesseract pillow

# For Tesseract (varies by OS)
# macOS:
brew install tesseract

# Linux:
sudo apt-get install tesseract-ocr

# Windows:
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
```

### Step 4: Update pyproject.toml

Add optional dependencies:

```toml
[project.optional-dependencies]
ocr = ["pytesseract>=0.3.10", "pillow>=9.0.0"]
doc = ["python-docx>=0.8.11"]
all = ["pytesseract>=0.3.10", "pillow>=9.0.0", "python-docx>=0.8.11"]
```

Install with:
```bash
pip install -e ".[ocr]"   # Just OCR
pip install -e ".[all]"   # All optional formats
```

### Step 5: Test Handler

Create a test script:

```python
# demo/scripts/test_handler.py

from src.handlers.input_handlers import InputHandlerFactory

# Test PDF
pdf_path = "demo/data/build_120/ENGINEERING/resume.pdf"
handler = InputHandlerFactory.get_handler(pdf_path)
text = handler.extract_text(pdf_path)
print(f"PDF extraction: {len(text)} characters")

# Test DOCX
docx_path = "demo/data/build_120/ENGINEERING/resume.docx"
handler = InputHandlerFactory.get_handler(docx_path)
text = handler.extract_text(docx_path)
print(f"DOCX extraction: {len(text)} characters")

# Test Image (if added)
# png_path = "demo/data/sample_cv.png"
# handler = InputHandlerFactory.get_handler(png_path)
# text = handler.extract_text(png_path)
# print(f"Image extraction: {len(text)} characters")
```

Run test:
```bash
python demo/scripts/test_handler.py
```

### Step 6: Use in Ingestion

The ingestion pipeline automatically detects and uses new handlers:

```bash
# Will automatically use ImageOCRHandler for .png files
python demo/scripts/ingest_cvs.py --input demo/data/build_120 --output output/all.csv
```

---

## 🔍 Handler Interface

All handlers must implement this interface:

```python
from abc import ABC, abstractmethod


class InputHandler(ABC):
    """Base interface for input handlers"""
    
    @classmethod
    @abstractmethod
    def extract_text(cls, file_path: str) -> str:
        """Extract raw text from file"""
        pass
    
    @classmethod
    @abstractmethod
    def validate(cls, file_path: str) -> bool:
        """Validate file format"""
        pass
    
    @classmethod
    @property
    @abstractmethod
    def supported_formats(cls) -> List[str]:
        """List of supported file extensions"""
        pass
```

---

## 📧 Example: Email Handler

Here's an example of adding email support:

```python
class EmailHandler:
    """Handler for email-based CVs (EML, MSG)"""
    
    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """Extract CV text from email attachment"""
        try:
            import email
            from email.parser import BytesParser
        except ImportError:
            raise ImportError("Email support requires Python stdlib email module")
        
        file_path = Path(file_path)
        
        # Parse email
        with open(file_path, 'rb') as f:
            msg = BytesParser().parsebytes(f.read())
        
        # Extract text from body
        text = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    text += part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            text = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        
        return text
    
    @classmethod
    def validate(cls, file_path: str) -> bool:
        path = Path(file_path)
        return path.suffix.lower() in ['.eml', '.msg']
    
    @classmethod
    @property
    def supported_formats(cls):
        return ['.eml', '.msg']


# Register it
InputHandlerFactory.register_handler(['.eml', '.msg'], EmailHandler)
```

---

## 🧪 Testing Checklist

After implementing a new handler:

- [ ] Handler class created and implements `InputHandler` interface
- [ ] Handler registered in `InputHandlerFactory`
- [ ] Dependencies listed in `pyproject.toml`
- [ ] Installation instructions documented
- [ ] Test script created and passing
- [ ] Sample file processed successfully
- [ ] Text extraction working
- [ ] Ingestion pipeline accepts new format
- [ ] CSV export includes new format files
- [ ] Dashboard displays results correctly
- [ ] No errors in extraction
- [ ] Documentation updated

---

## 🐛 Troubleshooting

### Import Error: Module not found
```
ImportError: No module named 'pytesseract'
```
**Solution**: Install the module
```bash
pip install pytesseract
```

### File Not Found
```
FileNotFoundError: tesseract is not installed
```
**Solution**: Install Tesseract system package (see Step 3)

### Invalid Format
```
ValueError: Unsupported format: .xyz
```
**Solution**: Register handler for the extension in `InputHandlerFactory`

### Extraction Quality Poor
- Check file is readable
- Try a different handler (if applicable)
- Validate file with system tools first
- Review extracted text for issues

---

## 📊 Performance Considerations

### Handler Performance Targets
- **PDF**: <100ms per page
- **DOCX**: <50ms per document
- **Images**: 1-5 seconds per image (OCR is slow)

### Optimization Tips
1. **Batch processing**: Process multiple files simultaneously
2. **Caching**: Store extracted text to avoid re-extraction
3. **Lazy loading**: Load models only when needed
4. **Async processing**: Use async for slow operations

### Example Optimized Handler
```python
class FastHandler:
    """Optimized handler with caching"""
    
    _cache = {}
    
    @classmethod
    def extract_text(cls, file_path: str) -> str:
        # Check cache first
        if file_path in cls._cache:
            return cls._cache[file_path]
        
        # Extract
        text = cls._do_extraction(file_path)
        
        # Cache result
        cls._cache[file_path] = text
        
        return text
```

---

## 🚀 Future Formats

Candidates for future support:

**High Priority** (demand exists):
- [ ] Word 97-2003 (.doc)
- [ ] Rich Text Format (.rtf)
- [ ] OpenOffice (.odt)
- [ ] Google Docs (API integration)

**Medium Priority** (nice to have):
- [ ] LaTeX (.tex)
- [ ] Markdown (.md)
- [ ] HTML (.html)
- [ ] LinkedIn profiles (API)

**Low Priority** (niche):
- [ ] EPUB (.epub)
- [ ] Image scans (PDF embedded)
- [ ] Video transcripts
- [ ] Audio transcripts

---

## 📚 References

### Useful Libraries
- **PDF**: `pdfplumber`, `PyPDF2`, `pypdf`
- **DOCX**: `python-docx`
- **Images**: `pytesseract`, `EasyOCR`, `Keras-OCR`
- **Email**: Python `email` module
- **Office**: `python-pptx`, `openpyxl`

### External Resources
- [pdfplumber docs](https://github.com/jsvine/pdfplumber)
- [python-docx docs](https://python-docx.readthedocs.io/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [pytesseract docs](https://github.com/madmaze/pytesseract)

---

## 📝 Handler Template

Use this as a starting point for new handlers:

```python
class MyFormatHandler:
    """Handler for [format] files"""
    
    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """Extract text from [format] file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # TODO: Implement extraction logic
        text = ""
        
        return text
    
    @classmethod
    def validate(cls, file_path: str) -> bool:
        """Validate file format"""
        path = Path(file_path)
        return path.suffix.lower() in ['.ext']
    
    @classmethod
    @property
    def supported_formats(cls):
        return ['.ext']
```

---

## ✅ Validation Guide

After adding a handler, validate with:

```bash
# 1. Test extraction
python -c "
from src.handlers.input_handlers import InputHandlerFactory
handler = InputHandlerFactory.get_handler('test.ext')
text = handler.extract_text('test.ext')
print(f'Extracted {len(text)} characters')
"

# 2. Test ingestion
python demo/scripts/ingest_cvs.py --input test_data --output test_output.csv

# 3. Check CSV
head -5 test_output.csv
wc -l test_output.csv

# 4. Test dashboard
streamlit run demo/src/dashboard/app.py
```

---

## 📞 Support

For issues with new handlers:
1. Check troubleshooting section above
2. Verify dependencies installed
3. Test handler in isolation
4. Check file format validity
5. Review error messages for hints

---

**Document Version**: 1.0  
**Last Updated**: March 20, 2026  
**Status**: Ready for Reference
