"""
Test real PDF files from sample/ directory
Saves markdown output to output/markdown/
"""

import os
import sys
from pathlib import Path

from src.extraction.pdf import PDFExtractor
from src.extraction.markdown import HybridSectionExtractor


def process_sample_pdfs():
    """Process all PDFs in sample/ and save markdown to output/markdown/"""
    sample_dir = Path("sample")
    output_dir = Path("output/markdown")
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = list(sample_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files in {sample_dir}")

    extractor = PDFExtractor()
    normalizer = HybridSectionExtractor()

    results = []
    for pdf_path in pdf_files:
        print(f"\nProcessing: {pdf_path.name}")

        pdf_result = extractor.extract(str(pdf_path))
        if not pdf_result.is_success:
            print(f"  [FAIL] PDF extraction failed: {pdf_result.error}")
            results.append({
                "file": pdf_path.name,
                "success": False,
                "error": pdf_result.error
            })
            continue

        normalized, metadata = normalizer.normalize(pdf_result.full_text)

        output_path = output_dir / f"{pdf_path.stem}.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(normalized)

        results.append({
            "file": pdf_path.name,
            "success": True,
            "pages": pdf_result.total_pages,
            "language": metadata.language_detected,
            "sections": metadata.sections_found,
            "confidence": metadata.confidence,
            "output": str(output_path)
        })

        print(f"  [OK] Pages: {pdf_result.total_pages}")
        print(f"     Language: {metadata.language_detected}")
        print(f"     Sections: {metadata.sections_found}")
        print(f"     Confidence: {metadata.confidence:.2f}")
        print(f"     Saved to: {output_path}")

    success_count = sum(1 for r in results if r["success"])
    print(f"\n{'='*50}")
    print(f"Summary: {success_count}/{len(results)} files processed successfully")
    print(f"Output directory: {output_dir}")

    return results


if __name__ == "__main__":
    results = process_sample_pdfs()
