#!/usr/bin/env python
"""
Batch CV Processing Script

Usage:
    python batch_cv_processing.py <input_dir> [--output-md <dir>] [--output-json <dir>] [--use-llm]

Example:
    python batch_cv_processing.py data/samples --output-md output/markdown --output-json output/json --use-llm
"""

import argparse
import sys
import logging
from pathlib import Path
import json
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction import CVParser, CVParsingConfig, LLMExtractionConfig, CVMarkdownConfig


def setup_logging(log_level=logging.INFO):
    """Configure logging."""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("cv_parsing.log"),
            logging.StreamHandler(),
        ],
    )


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Batch process CVs with robust parsing pipeline"
    )

    parser.add_argument(
        "input_dir",
        help="Input directory containing PDF files",
    )

    parser.add_argument(
        "--output-md",
        help="Output directory for markdown files",
        default="output/markdown",
    )

    parser.add_argument(
        "--output-json",
        help="Output directory for JSON files",
        default="output/json",
    )

    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use LLM extraction (requires Ollama running)",
    )

    parser.add_argument(
        "--model",
        default="qwen2.5-coder:3b",
        help="LLM model to use (default: qwen2.5-coder:3b)",
    )

    parser.add_argument(
        "--ollama-url",
        default="http://localhost:11434",
        help="Ollama service URL",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose logging",
    )

    return parser.parse_args()


def generate_report(results: list, output_file: str = "cv_parsing_report.json"):
    """Generate summary report of parsing results."""
    report = {
        "timestamp": datetime.now(datetime.timezone.utc).isoformat(),
        "total_files": len(results),
        "successful": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "results": [],
    }

    for result in results:
        result_summary = {
            "filename": result["filename"],
            "success": result["success"],
            "extraction_method": result["extraction_method"],
            "text_quality": result["text_quality"][0] if result["text_quality"] else None,
            "sections_detected": len(result["sections"]),
            "errors": result["errors"],
            "metadata": result["metadata"],
        }
        report["results"].append(result_summary)

    # Save report
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report


def print_report(report: dict):
    """Print parsing report to console."""
    print("\n" + "=" * 80)
    print("CV PARSING BATCH REPORT")
    print("=" * 80)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Total Files: {report['total_files']}")
    print(f"Successful: {report['successful']} ✓")
    print(f"Failed: {report['failed']} ✗")
    print(f"Success Rate: {report['successful'] / max(report['total_files'], 1) * 100:.1f}%")
    print("\nDetailed Results:")
    print("-" * 80)

    for result in report["results"]:
        status = "✓" if result["success"] else "✗"
        print(f"{status} {result['filename']}")
        if result["success"]:
            print(f"  Method: {result['extraction_method']}")
            print(f"  Sections: {result['sections_detected']}")
            print(f"  Text Quality: {'Valid' if result['text_quality'] else 'Invalid'}")
        else:
            if result["errors"]:
                print(f"  Errors: {'; '.join(result['errors'])}")

    print("=" * 80 + "\n")


def main():
    """Main entry point."""
    args = parse_arguments()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)

    logger = logging.getLogger(__name__)
    logger.info("Starting batch CV processing")

    # Validate input directory
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        logger.error(f"Input directory not found: {args.input_dir}")
        return 1

    pdf_count = len(list(input_dir.glob("*.pdf")))
    if pdf_count == 0:
        logger.warning(f"No PDF files found in {args.input_dir}")
        return 1

    logger.info(f"Found {pdf_count} PDF files to process")

    # Configure parser
    llm_config = None
    if args.use_llm:
        llm_config = LLMExtractionConfig(
            model_name=args.model,
            base_url=args.ollama_url,
        )
        logger.info(f"LLM extraction enabled: {args.model}")

    config = CVParsingConfig(
        use_llm_extraction=args.use_llm,
        llm_config=llm_config,
        output_markdown_dir=args.output_md,
        output_json_dir=args.output_json,
    )

    # Create parser
    parser = CVParser(config)

    # Process batch
    logger.info("Processing CVs...")
    results = parser.parse_batch(str(input_dir))

    # Generate report
    report = generate_report(results)

    # Save report
    report_file = "cv_parsing_report.json"
    generate_report(results, report_file)
    logger.info(f"Report saved to: {report_file}")

    # Print summary
    print_report(report)

    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
