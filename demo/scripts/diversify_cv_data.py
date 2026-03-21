"""
Data transformation script: Diversify CV formats across data/ folder
- Keeps original PDFs
- Converts copies to DOCX with TopCV template styling
- Splits proportionally (1/22 per template)
"""
import os
import shutil
import sys
from pathlib import Path
from typing import List, Tuple
import random
from datetime import datetime

# Add demo/src to path
demo_dir = Path(__file__).parent.parent
sys.path.insert(0, str(demo_dir))

from src.templates.template_manager import TemplateManager, TemplateStyle
from src.templates.converter import PDFToDocxConverter


class CVDataDiversifier:
    """Diversifies CV data across multiple formats and templates"""
    
    def __init__(self, data_root: str):
        self.data_root = Path(data_root)
        self.template_manager = TemplateManager()
        self.templates = list(self.template_manager.TEMPLATES.values())
        self.templates_count = len(self.templates)
        self.stats = {
            'categories_processed': 0,
            'pdfs_kept': 0,
            'pdfs_converted': 0,
            'docx_created': 0,
            'errors': 0
        }
    
    def get_categories(self) -> List[str]:
        """Get all job categories from data root"""
        categories = []
        for item in sorted(self.data_root.iterdir()):
            if item.is_dir() and not item.name.startswith('.'):
                categories.append(item.name)
        return categories
    
    def get_pdfs_in_category(self, category: str) -> List[Path]:
        """Get all PDF files in a category"""
        category_path = self.data_root / category
        pdfs = list(category_path.glob('*.pdf'))
        return sorted(pdfs)
    
    def split_and_assign_templates(self, pdf_list: List[Path], max_conversions: int = 10) -> List[Tuple[Path, int, str]]:
        """
        Split PDF list and assign templates round-robin (optimized for speed)
        
        Args:
            pdf_list: List of PDF paths
            max_conversions: Maximum files to convert per category (for speed)
        
        Returns list of (pdf_path, template_index, action) tuples
        where action is 'keep_pdf' or 'convert_docx'
        """
        assignments = []
        total_files = len(pdf_list)
        
        # Shuffle for randomness
        shuffled = pdf_list.copy()
        random.shuffle(shuffled)
        
        # Smart split: 
        # - Keep all files as PDF (no changes)
        # - Convert only a subset to DOCX for demonstration
        conversions_limit = min(max_conversions, max(1, total_files // 4))
        
        # Mark most PDFs to keep
        for pdf_path in shuffled:
            assignments.append((pdf_path, -1, 'keep_pdf'))
        
        # Assign templates to a subset for conversion (round-robin)
        for idx in range(conversions_limit):
            pdf_path = shuffled[idx]
            template_idx = idx % self.templates_count
            # Update the assignment for this PDF
            assignments[idx] = (pdf_path, template_idx, 'convert_docx')
        
        return assignments
    
    def process_category(self, category: str, dry_run: bool = False, max_conversions: int = 10) -> bool:
        """
        Process single category: diversify PDFs and create DOCX variants
        
        Args:
            category: Category name
            dry_run: If True, only show what would be done
            max_conversions: Maximum DOCX files to create per category
            
        Returns:
            True if successful
        """
        print(f"\n{'='*70}")
        print(f"Processing category: {category}")
        print(f"{'='*70}")
        
        category_path = self.data_root / category
        pdfs = self.get_pdfs_in_category(category)
        
        if not pdfs:
            print(f"  ⚠ No PDFs found in {category}")
            return False
        
        print(f"  Found {len(pdfs)} PDFs")
        
        # Get template assignments
        assignments = self.split_and_assign_templates(pdfs, max_conversions=max_conversions)
        
        # Group by action
        pdfs_keep = [a for a in assignments if a[2] == 'keep_pdf']
        pdfs_convert = [a for a in assignments if a[2] == 'convert_docx']
        
        print(f"  Action: Keep {len(pdfs_keep)} PDFs, Convert {len(pdfs_convert)} to DOCX")
        
        if dry_run:
            print(f"  [DRY RUN - No changes made]")
            self.stats['categories_processed'] += 1
            return True
        
        # Process conversions
        for pdf_path, template_idx, action in pdfs_convert:
            if template_idx < 0:
                continue
            
            try:
                template = self.templates[template_idx]
                
                # Create output DOCX path
                docx_filename = pdf_path.stem + f"_{template.name.replace(' ', '_')}.docx"
                docx_path = category_path / docx_filename
                
                print(f"    Converting: {pdf_path.name} → {template.name}...", end=" ")
                
                # Convert PDF to DOCX with template
                success = PDFToDocxConverter.pdf_to_docx_with_template(
                    str(pdf_path),
                    str(docx_path),
                    template
                )
                
                if success:
                    print("✓")
                    self.stats['docx_created'] += 1
                else:
                    print("✗")
                    self.stats['errors'] += 1
                    
            except Exception as e:
                print(f"✗ Error: {str(e)}")
                self.stats['errors'] += 1
        
        # Keep PDFs as-is (no action needed in filesystem, just count)
        self.stats['pdfs_kept'] += len(pdfs_keep)
        self.stats['categories_processed'] += 1
        
        return True
    
    def process_all_categories(self, dry_run: bool = False, max_conversions: int = 10):
        """Process all categories"""
        categories = self.get_categories()
        
        print(f"\n{'='*70}")
        print(f"CV Data Diversification Started")
        print(f"{'='*70}")
        print(f"Total templates available: {self.templates_count}")
        print(f"Total categories to process: {len(categories)}")
        print(f"Max DOCX conversions per category: {max_conversions}")
        print(f"Dry run: {dry_run}")
        print(f"{'='*70}")
        
        start_time = datetime.now()
        
        for category in categories:
            try:
                self.process_category(category, dry_run=dry_run, max_conversions=max_conversions)
            except Exception as e:
                print(f"  ERROR processing {category}: {str(e)}")
                self.stats['errors'] += 1
        
        # Print summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n{'='*70}")
        print("DIVERSIFICATION SUMMARY")
        print(f"{'='*70}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Categories processed: {self.stats['categories_processed']}")
        print(f"PDFs kept (original): {self.stats['pdfs_kept']}")
        print(f"DOCX files created: {self.stats['docx_created']}")
        print(f"Errors encountered: {self.stats['errors']}")
        print(f"{'='*70}\n")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Diversify CV data formats')
    parser.add_argument(
        '--data-root',
        type=str,
        default='/root/myproject/cv-filtering/data',
        help='Root directory containing category folders'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--category',
        type=str,
        help='Process only specific category'
    )
    parser.add_argument(
        '--max-conversions',
        type=int,
        default=10,
        help='Maximum DOCX conversions per category (for speed)'
    )
    
    args = parser.parse_args()
    
    diversifier = CVDataDiversifier(args.data_root)
    
    if args.category:
        diversifier.process_category(args.category, dry_run=args.dry_run, max_conversions=args.max_conversions)
    else:
        diversifier.process_all_categories(dry_run=args.dry_run, max_conversions=args.max_conversions)


if __name__ == '__main__':
    main()
