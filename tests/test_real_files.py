"""
Test real PDF files from sample/ directory
Saves markdown output to output/markdown/
"""

from pathlib import Path

from src.extraction import PDFExtractor
from src.extraction.markdown import HybridSectionExtractor


def process_sample_pdfs():
    """Process all PDFs in sample/ and save markdown to output/markdown/"""
    sample_dir = Path("sample")
    output_dir = Path("output/markdown")
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = list(sample_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files in {sample_dir}")

    normalizer = HybridSectionExtractor()

    results = []
    for pdf_path in pdf_files:
        print(f"\nProcessing: {pdf_path.name}")

        success, text, method = PDFExtractor.extract_text_with_fallback(str(pdf_path))
        if not success:
            print(f"  [FAIL] PDF extraction failed with method: {method}")
            results.append({
                "file": pdf_path.name,
                "success": False,
                "error": "Extraction failed"
            })
            continue

        normalized, metadata = normalizer.normalize(text)

        output_path = output_dir / f"{pdf_path.stem}.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(normalized)

        results.append({
            "file": pdf_path.name,
            "success": True,
            "method": method,
            "language": metadata.language_detected,
            "sections": metadata.sections_found,
            "confidence": metadata.confidence,
            "output": str(output_path)
        })

        print(f"  [OK] Method: {method}")
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
