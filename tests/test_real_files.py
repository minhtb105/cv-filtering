"""
Test real PDF files from sample/ directory
Saves markdown output to output/markdown/
"""

# import sys
# sys.path.insert(0, '.')

from pathlib import Path
from src.extraction.cv_parser import CVParser


def process_sample_pdfs():
    """Process all PDFs in sample/ and save markdown to output/markdown/"""
    sample_dir = Path("sample")
    output_dir = Path("output/markdown")
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = list(sample_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files in {sample_dir}")

    parser = CVParser()

    results = []
    for pdf_path in pdf_files:
        print(f"\nProcessing: {pdf_path.name}")

        result = parser.parse_cv(str(pdf_path))
        if not result["success"]:
            print(f"  [FAIL] PDF parsing failed: {result['errors']}")
            results.append({
                "file": pdf_path.name,
                "success": False,
                "error": "Parsing failed"
            })
            continue

        normalized = result["markdown"]
        metadata = {
            "language_detected": result.get("language", "unknown"),
            "sections_found": len(result.get("extracted_profile", {}) or {}),
            "confidence": 0.95  # Default confidence since we don't have the original confidence metric
        }

        output_path = output_dir / f"{pdf_path.stem}.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(normalized)

        results.append({
            "file": pdf_path.name,
            "success": True,
            "method": "clean_architecture_pipeline",
            "language": metadata["language_detected"],
            "sections": metadata["sections_found"],
            "confidence": metadata["confidence"],
            "output": str(output_path)
        })

        print(f"  [OK] Method: clean_architecture_pipeline")
        print(f"     Language: {metadata['language_detected']}")
        print(f"     Sections: {metadata['sections_found']}")
        print(f"     Confidence: {metadata['confidence']:.2f}")
        print(f"     Saved to: {output_path}")

    success_count = sum(1 for r in results if r["success"])
    print(f"\n{'='*50}")
    print(f"Summary: {success_count}/{len(results)} files processed successfully")
    print(f"Output directory: {output_dir}")

    return results


if __name__ == "__main__":
    results = process_sample_pdfs()
    