#!/usr/bin/env python
"""
Test script for the 5-step CV processing pipeline.

Tests:
  - STEP 1-4: Geometric extraction (PDFExtractor)
  - STEP 5A: NO-LLM section extraction
  - STEP 5B: LLM section extraction (optional)
  - Full integration via CVProcessingPipeline
"""

import os
import sys
import logging
from pathlib import Path

# Setup project path - handle both script and module execution
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.extraction.pdf_extractor import PDFExtractor, ExtractionResult
from src.extraction.cv_reading_order import CVReadingOrder, ExtractionMode
from src.extraction.cv_pipeline_integration import CVProcessingPipeline, PipelineConfig
from src.extraction.cv_parser import CVParser, CVParsingConfig


def test_pdf_extractor_steps_1_4():
    """Test STEPS 1-4: Geometric extraction."""
    print("\n" + "=" * 60)
    print("TEST: PDFExtractor (STEPS 1-4: Geometric Extraction)")
    print("=" * 60)
    
    # Find a sample PDF
    sample_pdfs = list(Path("data").glob("*/*.pdf"))
    if not sample_pdfs:
        logger.warning("No PDF files found in data/ directory")
        return False
    
    pdf_path = str(sample_pdfs[0])
    logger.info(f"Testing with: {pdf_path}")
    
    try:
        extractor = PDFExtractor()
        result = extractor.extract(pdf_path)
        
        logger.info(f"✓ Extraction successful")
        logger.info(f"  - Pages: {result.total_pages}")
        logger.info(f"  - Intermediate markdown size: {len(result.intermediate_markdown)} chars")
        logger.info(f"  - Ordered text size: {len(result.full_text)} chars")
        
        # Display sample output
        if result.intermediate_markdown:
            print("\n--- Sample Intermediate Markdown (first 500 chars) ---")
            print(result.intermediate_markdown[:500])
            print("...\n")
        
        return result.is_success
    
    except Exception as e:
        logger.error(f"✗ Extraction failed: {e}", exc_info=True)
        return False


def test_cv_reading_order_no_llm():
    """Test STEP 5A: NO-LLM extraction."""
    print("\n" + "=" * 60)
    print("TEST: CVReadingOrder NO-LLM (STEP 5A)")
    print("=" * 60)
    
    # Find a sample PDF
    sample_pdfs = list(Path("data").glob("*/*.pdf"))
    if not sample_pdfs:
        logger.warning("No PDF files found in data/ directory")
        return False
    
    pdf_path = str(sample_pdfs[0])
    
    try:
        # First extract intermediate markdown
        extractor = PDFExtractor()
        result = extractor.extract(pdf_path)
        if not result.is_success:
            logger.error("Failed to extract PDF")
            return False
        
        # Then extract sections NO-LLM
        reading_order = CVReadingOrder(mode=ExtractionMode.NO_LLM)
        sections = reading_order.extract(result.intermediate_markdown)
        
        logger.info(f"✓ NO-LLM extraction successful")
        logger.info(f"  - Sections found: {len(sections)}")
        
        for section_type, section_data in sections.items():
            content_preview = section_data.content[:100].replace("\n", " ") + "..."
            logger.info(f"    • {section_type}: {content_preview}")
        
        return len(sections) > 0
    
    except Exception as e:
        logger.error(f"✗ NO-LLM extraction failed: {e}", exc_info=True)
        return False


def test_full_pipeline():
    """Test full pipeline integration."""
    print("\n" + "=" * 60)
    print("TEST: Full CVProcessingPipeline")
    print("=" * 60)
    
    # Find a sample PDF
    sample_pdfs = list(Path("data").glob("*/*.pdf"))
    if not sample_pdfs:
        logger.warning("No PDF files found in data/ directory")
        return False
    
    pdf_path = str(sample_pdfs[0])
    logger.info(f"Testing with: {pdf_path}")
    
    try:
        # Create output directories
        output_dir = Path("output/test_pipeline")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        config = PipelineConfig(
            use_llm=False,  # NO-LLM mode for this test
            output_markdown_dir=str(output_dir / "markdown"),
            output_json_dir=str(output_dir / "json"),
            debug=False
        )
        
        pipeline = CVProcessingPipeline(config=config)
        result = pipeline.process_pdf(pdf_path)
        
        logger.info(f"✓ Pipeline successful: {result.success}")
        logger.info(f"  - Filename: {result.filename}")
        logger.info(f"  - Total pages: {result.total_pages}")
        logger.info(f"  - Sections found: {len(result.extracted_sections)}")
        logger.info(f"  - Extraction mode: {result.metadata.get('extraction_mode', 'unknown')}")
        
        # Show extracted sections
        if result.extracted_sections:
            print("\n--- Extracted Sections ---")
            for section_type, section_data in result.extracted_sections.items():
                preview = section_data.content[:80].replace("\n", " ") + "..."
                confidence = f"{section_data.confidence:.0%}"
                logger.info(f"  • {section_type} ({confidence}): {preview}")
        
        # Check outputs
        markdown_files = list(output_dir.glob("markdown/*.md"))
        json_files = list(output_dir.glob("json/*.json"))
        
        logger.info(f"\n  - Markdown files saved: {len(markdown_files)}")
        logger.info(f"  - JSON files saved: {len(json_files)}")
        
        return result.success
    
    except Exception as e:
        logger.error(f"✗ Pipeline failed: {e}", exc_info=True)
        return False


def test_cv_parser_integration():
    """Test CVParser integration with new pipeline."""
    print("\n" + "=" * 60)
    print("TEST: CVParser Integration (High-Level API)")
    print("=" * 60)
    
    # Find a sample PDF
    sample_pdfs = list(Path("data").glob("*/*.pdf"))
    if not sample_pdfs:
        logger.warning("No PDF files found in data/ directory")
        return False
    
    pdf_path = str(sample_pdfs[0])
    logger.info(f"Testing with: {pdf_path}")
    
    try:
        output_dir = Path("output/test_parser")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        config = CVParsingConfig(
            use_llm_extraction=False,
            output_markdown_dir=str(output_dir / "markdown"),
            output_json_dir=str(output_dir / "json"),
        )
        
        parser = CVParser(config=config)
        result = parser.parse_cv(pdf_path)
        
        logger.info(f"✓ CVParser success: {result['success']}")
        logger.info(f"  - Filename: {result['filename']}")
        logger.info(f"  - Extraction method: {result['extraction_method']}")
        logger.info(f"  - Sections found: {len(result['sections'])}")
        logger.info(f"  - Errors: {len(result['errors'])}")
        
        if result['sections']:
            print("\n--- Sections from CVParser ---")
            for section_type, content in result['sections'].items():
                preview = content[:60].replace("\n", " ") + "..." if isinstance(content, str) else str(content)[:60]
                logger.info(f"  • {section_type}: {preview}")
        
        if result['markdown']:
            print("\n--- Generated Markdown (first 300 chars) ---")
            print(result['markdown'][:300])
            print("...\n")
        
        return result['success']
    
    except Exception as e:
        logger.error(f"✗ CVParser failed: {e}", exc_info=True)
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("5-STEP CV PIPELINE - VALIDATION TESTS")
    print("=" * 60)
    
    tests = [
        ("STEPS 1-4 (Geometric Extraction)", test_pdf_extractor_steps_1_4),
        ("STEP 5A (NO-LLM Extraction)", test_cv_reading_order_no_llm),
        ("Full Pipeline Integration", test_full_pipeline),
        ("CVParser High-Level API", test_cv_parser_integration),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for p in results.values() if p)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
