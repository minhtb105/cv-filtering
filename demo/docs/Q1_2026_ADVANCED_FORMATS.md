# Q1 2026 - Advanced Format Support

## 🎯 Objective
Extend CV Intelligence Platform to support additional document formats beyond PDF, enabling broader applicant coverage and reducing parsing friction.

## 📋 Task Breakdown

### Task 1: Image-Based CV Parsing (OCR) - Week 1-2
**Objective**: Extract text from image-format CVs (JPEG, PNG, TIFF)

**Technical Approach**:
```python
# pytesseract for OCR
# pillow for image processing
# auto-rotate for sideways scans

class ImageCVParser(CVParser):
    def parse(self, file_path: str) -> StructuredProfile:
        # Detect orientation
        self.rotate_if_needed(file_path)
        
        # Extract text via OCR
        raw_text = pytesseract.image_to_string(Image.open(file_path))
        
        # Normalize + parse as text
        return self.parse_text(raw_text)
```

**Deliverables**:
- [ ] OCR parser implementation
- [ ] Image rotation detection
- [ ] Quality assessment (character confidence)
- [ ] Tests for 10+ image formats
- [ ] Performance: <2s per image

**Dependencies to Add**:
- pytesseract==0.3.13
- Pillow>=10.0
- python-tesseract (system)

---

### Task 2: Email Resume Parsing - Week 2-3
**Objective**: Extract CVs from email attachments and body content

**Technical Approach**:
```python
class EmailHandler(CVHandler):
    def extract(self, email_content: str) -> Dict[str, any]:
        # Parse email headers
        from email.parser import Parser
        msg = Parser().parsestr(email_content)
        
        # Extract attachments
        for part in msg.walk():
            if part.get_content_disposition() == 'attachment':
                filename = part.get_filename()
                payload = part.get_payload(decode=True)
                # Route to appropriate parser
        
        # Extract body text (signature removal)
        body = self.remove_email_signature(msg.get_payload())
        
        return {
            'attachments': parsed_attachments,
            'body_profile': self.parse_text(body),
            'metadata': {
                'from': msg['From'],
                'date': msg['Date'],
                'subject': msg['Subject']
            }
        }
```

**Deliverables**:
- [ ] Email parser (EML, MSG formats)
- [ ] Attachment extraction
- [ ] Email signature removal
- [ ] MIME type routing
- [ ] Tests for 5+ email formats
- [ ] Performance: <500ms per email

**Dependencies to Add**:
- python-email-validator==2.1
- email-validator>=2.1
- extract-msg>=0.48.0 (Outlook)

---

### Task 3: Legacy Document Support - Week 3-4
**Objective**: Parse legacy CV formats (DOC, RTF, XLS)

**Technical Approach**:
```python
class LegacyDocumentHandler(CVHandler):
    def extract(self, file_path: str) -> StructuredProfile:
        ext = Path(file_path).suffix.lower()
        
        if ext == '.doc':
            return self.parse_doc(file_path)
        elif ext == '.docx':
            return self.parse_docx(file_path)
        elif ext == '.rtf':
            return self.parse_rtf(file_path)
        elif ext in ['.xls', '.xlsx']:
            return self.parse_spreadsheet(file_path)
        else:
            raise UnsupportedFormatError(f"Format {ext} not supported")
    
    def parse_doc(self, file_path: str) -> StructuredProfile:
        # Use python-docx or docx2txt
        # Strip formatting, extract text
        pass
    
    def parse_rtf(self, file_path: str) -> StructuredProfile:
        # Use striprtf or panflute
        # Extract text, normalize
        pass
```

**Deliverables**:
- [ ] DOC/DOCX support (python-docx)
- [ ] RTF support (striprtf)
- [ ] XLS/XLSX support (openpyxl, xlrd)
- [ ] Format conversion pipeline
- [ ] Tests for 8+ legacy formats
- [ ] Performance: <1s per document
- [ ] Fallback to text extraction

**Dependencies to Add**:
- python-docx>=0.8.11
- striprtf>=0.0.26
- openpyxl>=3.10
- xlrd>=2.0

---

## 📊 Format Support Matrix

| Format | Current | Q1 2026 | Parser | Speed |
|--------|---------|---------|--------|-------|
| PDF | ✓ | ✓ | PyPDF2 | <1s |
| DOCX | ✗ | ✓ | python-docx | <1s |
| DOC | ✗ | ✓ | python-docx | <1s |
| RTF | ✗ | ✓ | striprtf | <500ms |
| XLS/XLSX | ✗ | ✓ | openpyxl | <500ms |
| JPG/PNG | ✗ | ✓ | pytesseract | <2s |
| TIFF | ✗ | ✓ | pytesseract | <2s |
| EML | ✗ | ✓ | email.parser | <500ms |
| MSG | ✗ | ✓ | extract-msg | <1s |

**Target**: Support 9 formats (+8 vs current 1)

---

## 🔧 Implementation Structure

```
demo/src/
├── handlers/
│   ├── image_handler.py          [NEW]
│   ├── email_handler.py          [NEW]
│   ├── legacy_handler.py         [NEW]
│   └── input_handlers.py         [REFACTOR]
│
├── extraction/
│   ├── image_parser.py           [NEW]
│   ├── email_parser.py           [NEW]
│   ├── legacy_parser.py          [NEW]
│   └── parser.py                 [UPDATE ROUTER]
│
└── utils/
    ├── format_detector.py        [NEW - auto-detect format]
    ├── image_processor.py        [NEW - OCR preprocessing]
    └── email_utils.py            [NEW - signature removal]

demo/tests/
├── test_image_parsing.py         [NEW]
├── test_email_parsing.py         [NEW]
├── test_legacy_parsing.py        [NEW]
└── test_format_integration.py    [NEW]
```

---

## 📈 Success Metrics

**Coverage**:
- ✓ Support 9 file formats (vs 1 today)
- ✓ Handle 95% of common CV layouts
- ✓ Accuracy within 2% of PDF parsing

**Performance**:
- ✓ Image OCR: <2 seconds per file
- ✓ Email parsing: <500ms per email
- ✓ Legacy documents: <1 second per file
- ✓ Format detection: <100ms

**Quality**:
- ✓ Zero breaking changes to existing code
- ✓ 95%+ unit test coverage for new handlers
- ✓ Error resilience (graceful fallbacks)
- ✓ Comprehensive error messages

---

## 🚀 Deployment Checklist

- [ ] All parsers implemented
- [ ] Unit tests pass (>95% coverage)
- [ ] Integration tests with real documents
- [ ] Performance benchmarks within targets
- [ ] Error handling tested
- [ ] Documentation updated
- [ ] Migration guide created
- [ ] Dashboard updated with format indicators
- [ ] CSV export includes format metadata
- [ ] Deployment scripts updated

---

## 📚 Dependencies Summary

```txt
# Image OCR Support
pytesseract==0.3.13
Pillow>=10.0

# Email Parsing
email-validator>=2.1
extract-msg>=0.48.0

# Legacy Document Support
python-docx>=0.8.11
striprtf>=0.0.26
openpyxl>=3.10
xlrd>=2.0
```

**Total new dependencies**: 9
**Estimated size increase**: ~50MB

---

## 🎯 Week-by-Week Timeline

**Week 1-2**: Image OCR Support
- Days 1-3: Implementation (ImageCVParser, rotation detection)
- Days 4-5: Testing (unit + integration), performance tuning
- Day 6-7: Documentation, merged to main

**Week 2-3**: Email Resume Parsing
- Days 1-3: Implementation (EmailHandler, signature removal)
- Days 4-5: Testing, format support expansion
- Days 6-7: Documentation, merged to main

**Week 3-4**: Legacy Document Support
- Days 1-3: Implementation (DOC, RTF, XLS support)
- Days 4-5: Testing, format matrix validation
- Days 6-7: Documentation, final integration tests

**Week 4**: Integration & Polish
- Day 1-2: Cross-format testing
- Day 3-4: Performance optimization
- Day 5-7: Documentation, deployment

---

## 💡 Implementation Notes

1. **Format Detection**: Auto-detect format by file extension + magic bytes
2. **Graceful Degradation**: If OCR fails, fallback to text extraction
3. **Email Attachments**: Support nested attachments, multiple formats
4. **Legacy Formats**: Preserve formatting where possible (bullet points, sections)
5. **Caching**: Cache parsed documents (same logic as Day 5)
6. **Monitoring**: Track parsing success rate by format

---

## 🔗 Related Documentation
- [DAY_5_PLAN.md](./DAY_5_PLAN.md) - Current optimization status
- [FEATURE_ROADMAP.md](./FEATURE_ROADMAP.md) - Q2-Q4 plans
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Production deployment
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues
