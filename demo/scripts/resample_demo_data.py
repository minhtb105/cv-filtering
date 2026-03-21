"""
Demo data resampling script: Clear demo/data and resample fresh diverse data
"""
import os
import shutil
import sys
from pathlib import Path
from typing import List
import random

demo_dir = Path(__file__).parent.parent
sys.path.insert(0, str(demo_dir))


class DemoDataResampler:
    """Resamples demo/data with fresh diverse CV data"""
    
    def __init__(self, data_root: str, demo_data_root: str):
        self.data_root = Path(data_root)
        self.demo_data_root = Path(demo_data_root)
    
    def clear_demo_data(self) -> bool:
        """Clear all directories in demo/data"""
        try:
            if not self.demo_data_root.exists():
                self.demo_data_root.mkdir(parents=True, exist_ok=True)
                return True
            
            print(f"Clearing {self.demo_data_root}...", end=" ")
            
            # Remove all subdirectories
            for item in self.demo_data_root.iterdir():
                if item.is_dir():
                    print(f"\n  Removing {item.name}...", end=" ")
                    shutil.rmtree(item)
                    print("✓")
            
            print("✓ Demo data cleared")
            return True
            
        except Exception as e:
            print(f"✗ Error clearing demo data: {str(e)}")
            return False
    
    def resample_data(self, sample_size: int = 5, sample_name: str = "sample_1") -> bool:
        """
        Resample diverse data from all categories
        Creates category-wise distribution in demo/data
        
        Args:
            sample_size: Files to sample per category
            sample_name: Name of the sample subdirectory
        """
        try:
            # Create sample directory
            sample_dir = self.demo_data_root / sample_name
            sample_dir.mkdir(parents=True, exist_ok=True)
            
            # Get current sample size to ensure diversity
            total_files_to_copy = 0
            
            # First pass: count files
            categories = sorted([d for d in self.data_root.iterdir() if d.is_dir()])
            for category in categories:
                files = list(category.glob('*pdf')) + list(category.glob('*.docx'))
                total_files_to_copy += min(len(files), sample_size)
            
            print(f"\nResampling demo data ({sample_name})")
            print(f"{'='*70}")
            print(f"Target directory: {sample_dir}")
            print(f"Estimated files to copy: {total_files_to_copy}")
            print(f"Files per category: ~{sample_size}")
            print(f"{'='*70}")
            
            copied_count = 0
            
            # Second pass: copy files
            for category in categories:
                category_name = category.name
                
                # Get all files (both PDF and DOCX)
                pdf_files = list(category.glob('*.pdf'))
                docx_files = list(category.glob('*.docx'))
                all_files = pdf_files + docx_files
                
                if not all_files:
                    print(f"  {category_name}: No files found")
                    continue
                
                # Sample files ensuring format diversity
                to_sample = min(sample_size, len(all_files))
                
                # Try to get mix of PDF and DOCX
                sampled = random.sample(all_files, to_sample)
                
                print(f"  {category_name}:", end=" ")
                
                for file_path in sampled:
                    try:
                        dest = sample_dir / f"{category_name}_{file_path.name}"
                        shutil.copy2(file_path, dest)
                        copied_count += 1
                    except Exception as e:
                        print(f"\n    Error copying {file_path.name}: {str(e)}")
                
                print(f"✓ ({len(sampled)} files)")
            
            print(f"\n{'='*70}")
            print(f"Total files copied: {copied_count}")
            print(f"{'='*70}\n")
            
            return True
            
        except Exception as e:
            print(f"\n✗ Error resampling data: {str(e)}\n")
            return False
    
    def recreate_embeddings_structure(self) -> bool:
        """Recreate embeddings and vector_index directories"""
        try:
            embeddings_dir = self.demo_data_root / "embeddings"
            vector_index_dir = self.demo_data_root / "vector_index"
            
            print("Creating directory structure for embeddings and vector index...")
            embeddings_dir.mkdir(parents=True, exist_ok=True)
            vector_index_dir.mkdir(parents=True, exist_ok=True)
            
            print("  embeddings/ ✓")
            print("  vector_index/ ✓")
            print()
            
            return True
        except Exception as e:
            print(f"Error creating directories: {str(e)}")
            return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Resample demo/data with fresh diverse data')
    parser.add_argument(
        '--data-root',
        type=str,
        default='/root/myproject/cv-filtering/data',
        help='Root directory containing diversified categories'
    )
    parser.add_argument(
        '--demo-data-root',
        type=str,
        default='/root/myproject/cv-filtering/demo/data',
        help='Demo data directory to resample into'
    )
    parser.add_argument(
        '--sample-size',
        type=int,
        default=5,
        help='Number of files to sample per category'
    )
    parser.add_argument(
        '--sample-name',
        type=str,
        default='sample_1',
        help='Name of sample directory'
    )
    parser.add_argument(
        '--skip-clear',
        action='store_true',
        help='Skip clearing existing demo/data'
    )
    
    args = parser.parse_args()
    
    resampler = DemoDataResampler(args.data_root, args.demo_data_root)
    
    # Step 1: Clear demo data
    if not args.skip_clear:
        resampler.clear_demo_data()
    
    # Step 2: Resample fresh data
    resampler.resample_data(
        sample_size=args.sample_size,
        sample_name=args.sample_name
    )
    
    # Step 3: Recreate directory structure
    resampler.recreate_embeddings_structure()


if __name__ == '__main__':
    main()
