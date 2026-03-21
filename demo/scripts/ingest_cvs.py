"""
Main ingestion script: Process CVs and export to CSV
This is the Day 1 MVP for testing
"""
import sys
from pathlib import Path
from datetime import datetime
import hashlib
import csv
from typing import List

# Add src to path
demo_dir = Path(__file__).parent.parent
sys.path.insert(0, str(demo_dir / "src"))

from models import Candidate, CVVersion, StructuredProfile
from handlers.input_handlers import InputHandlerFactory
from extraction.parser import CVExtractor


def get_file_hash(file_path: str) -> str:
    """Generate unique ID from file"""
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()[:12]


def ingest_cv(file_path: str, category: str, extractor: CVExtractor) -> Candidate:
    """Ingest single CV file and return Candidate object"""
    
    # Get handler
    handler = InputHandlerFactory.get_handler(file_path)
    
    # Extract text
    print(f"  Extracting text: {Path(file_path).name}...", end=" ")
    try:
        raw_text = handler.extract_text(file_path)
    except Exception as e:
        print(f"FAILED: {e}")
        raise
    
    # Extract structured data
    print("parsing...", end=" ")
    extracted = extractor.extract_all(raw_text)
    
    # Convert to proper dataclass objects
    from models import ContactInfo, Experience, Education
    
    contact = ContactInfo(**extracted["contact"])
    experiences = [Experience(**exp) for exp in extracted["experiences"]]
    education_list = [Education(**edu) for edu in extracted["education"]]
    
    # Create structured profile
    structured = StructuredProfile(
        contact=contact,
        summary=extracted["summary"],
        skills=extracted["skills"],
        experiences=experiences,
        education=education_list,
        languages=extracted["languages"],
        years_experience=extracted["years_experience"],
    )
    
    # Create CV version
    candidate_id = f"cand_{get_file_hash(file_path)}"
    version_id = f"v1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    cv_version = CVVersion(
        version_id=version_id,
        file_name=Path(file_path).name,
        file_path=file_path,
        raw_text=raw_text,
        structured_data=structured,
        file_format=Path(file_path).suffix.lower().lstrip('.')
    )
    
    # Create candidate
    candidate = Candidate(
        candidate_id=candidate_id,
        cv_versions=[cv_version],
        category=category
    )
    
    print("OK")
    return candidate


def batch_ingest(data_dir: str, output_csv: str, limit: int = None) -> List[Candidate]:
    """Batch ingest all CVs from data directory"""
    data_path = Path(data_dir)
    candidates = []
    failed = []
    
    print(f"\n{'='*60}")
    print(f"Starting batch ingestion from {data_dir}")
    print(f"Output CSV: {output_csv}")
    print(f"{'='*60}\n")
    
    # Initialize extractor
    print("Loading spaCy model...")
    extractor = CVExtractor()
    
    # Get all CV files grouped by category
    files_by_category = {}
    
    # If data_dir has subdirectories, treat as categories
    if any(d.is_dir() for d in data_path.iterdir()):
        for cat_dir in sorted(data_path.iterdir()):
            if cat_dir.is_dir():
                files = list(cat_dir.glob("*.pdf")) + list(cat_dir.glob("*.docx"))
                if files:
                    files_by_category[cat_dir.name] = files
    else:
        # Flat structure, infer category from some other means
        files = list(data_path.glob("*.pdf")) + list(data_path.glob("*.docx"))
        files_by_category["UNCATEGORIZED"] = files
    
    total_files = sum(len(f) for f in files_by_category.values())
    print(f"Found {total_files} files across {len(files_by_category)} categories\n")
    
    # Process each category
    processed = 0
    for category, files in sorted(files_by_category.items()):
        print(f"[{category}] Processing {len(files)} files...")
        
        for file_path in files:
            if limit and processed >= limit:
                break
            
            try:
                candidate = ingest_cv(str(file_path), category, extractor)
                candidates.append(candidate)
                processed += 1
            except Exception as e:
                failed.append((str(file_path), str(e)))
                print(f"    ERROR: {e}")
        
        if limit and processed >= limit:
            break
    
    # Export to CSV
    print(f"\n{'='*60}")
    print(f"Exporting {len(candidates)} candidates to CSV...")
    print(f"{'='*60}\n")
    
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'candidate_id', 'category', 'name', 'email', 'phone', 'location',
            'skills', 'years_experience', 'file_name', 'created_at'
        ])
        writer.writeheader()
        
        for candidate in candidates:
            latest = candidate.latest_version
            if latest:
                contact = latest.structured_data.contact
                writer.writerow({
                    'candidate_id': candidate.candidate_id,
                    'category': candidate.category,
                    'name': contact.name or 'N/A',
                    'email': contact.email or 'N/A',
                    'phone': contact.phone or 'N/A',
                    'location': contact.location or 'N/A',
                    'skills': ' | '.join(candidate.skills[:10]),
                    'years_experience': latest.structured_data.years_experience,
                    'file_name': latest.file_name,
                    'created_at': latest.created_at.isoformat()
                })
    
    # Summary
    print(f"\n{'='*60}")
    print(f"INGESTION SUMMARY")
    print(f"{'='*60}")
    print(f"✓ Processed: {processed}")
    print(f"✗ Failed: {len(failed)}")
    print(f"→ Output CSV: {output_csv}")
    
    if failed:
        print(f"\nFailed files:")
        for file_path, error in failed[:5]:
            print(f"  - {Path(file_path).name}: {error[:50]}")
        if len(failed) > 5:
            print(f"  ... and {len(failed) - 5} more")
    
    print(f"{'='*60}\n")
    
    return candidates


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest CVs")
    parser.add_argument("--input", default="data/sample_1", help="Input directory")
    parser.add_argument("--output", help="Output CSV file")
    parser.add_argument("--limit", type=int, help="Limit number of files to process")
    
    args = parser.parse_args()
    
    # Default output based on input
    if not args.output:
        input_name = Path(args.input).name
        args.output = f"output/{input_name}_extracted.csv"
    
    # Create output directory
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    # Run ingestion
    candidates = batch_ingest(args.input, args.output, args.limit)
    print(f"\nDone! Check output at {args.output}")
