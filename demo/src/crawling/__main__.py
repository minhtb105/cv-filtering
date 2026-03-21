"""
Main entry point for the Job Description Crawler

Provides command-line interface and main orchestration logic for crawling
job descriptions from various sources.
"""

import asyncio
import argparse
import logging
from typing import List, Dict, Any
import json
from src.models import JobDescription, CATEGORY_MAPPING
from src.crawling.mcp_crawler import MCPCrawler, crawl_jobs
from src.crawling.exporters import JobDescriptionExporter
from src.crawling.validators import JobDescriptionValidator


class JDCCrawlerOrchestrator:
    """Main orchestrator for the Job Description Crawler"""
    
    def __init__(self, output_dir: str = "output", mcp_server: str = "playwright"):
        self.output_dir = output_dir
        self.mcp_server = mcp_server
        self.logger = self._setup_logging()
        self.validator = JobDescriptionValidator()
        self.exporter = JobDescriptionExporter(output_dir)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('crawler.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    def get_available_categories(self) -> List[str]:
        """Get list of available categories"""
        return list(CATEGORY_MAPPING.keys())
    
    def validate_categories(self, categories: List[str]) -> List[str]:
        """Validate and filter categories"""
        available_categories = self.get_available_categories()
        valid_categories = []
        
        for category in categories:
            if category in available_categories:
                valid_categories.append(category)
            else:
                self.logger.warning(f"Unknown category: {category}. Available: {available_categories}")
        
        return valid_categories
    
    async def crawl_categories(self, categories: List[str], location: str = "Vietnam", 
                              limit_per_category: int = 25) -> Dict[str, List[JobDescription]]:
        """Crawl multiple categories"""
        self.logger.info(f"Starting crawl for categories: {categories}")
        self.logger.info(f"Location: {location}, Limit per category: {limit_per_category}")
        
        # Validate categories
        valid_categories = self.validate_categories(categories)
        
        if not valid_categories:
            self.logger.error("No valid categories provided")
            return {}
        
        # Initialize crawler
        crawler = MCPCrawler(self.mcp_server)
        
        try:
            # Crawl jobs
            results = await crawler.crawl_multiple_categories(
                valid_categories, location, limit_per_category
            )
            
            self.logger.info(f"Crawling completed. Results: {len(results)} categories")
            
            # Validate results
            validated_results = {}
            for category, jobs in results.items():
                validated_jobs = []
                for job in jobs:
                    if self.validator.validate_job_description(job):
                        validated_jobs.append(job)
                    else:
                        self.logger.warning(f"Invalid job description found: {job.title}")
                
                validated_results[category] = validated_jobs
                self.logger.info(f"Category {category}: {len(validated_jobs)} valid jobs")
            
            return validated_results
            
        finally:
            await crawler.close()
    
    def export_results(self, results: Dict[str, List[JobDescription]], 
                      export_format: str = "json", export_summary: bool = True) -> Dict[str, str]:
        """Export crawling results"""
        exported_files = {}
        
        # Export by category
        if export_format.lower() in ["json", "csv"]:
            category_files = self.exporter.export_by_category(results, export_format.lower())
            exported_files.update(category_files)
            self.logger.info(f"Exported category files: {list(category_files.keys())}")
        
        # Export summary report
        if export_summary:
            summary_file = self.exporter.export_summary_report(results)
            exported_files["summary"] = summary_file
            self.logger.info(f"Exported summary report: {summary_file}")
        
        # Export combined results
        all_jobs = []
        for jobs in results.values():
            all_jobs.extend(jobs)
        
        if all_jobs:
            if export_format.lower() == "json":
                combined_file = self.exporter.export_to_json(all_jobs, "all_jobs.json")
            elif export_format.lower() == "csv":
                combined_file = self.exporter.export_to_csv(all_jobs, "all_jobs.csv")
            else:
                combined_file = self.exporter.export_for_api(all_jobs, "api_jobs.json")
            
            exported_files["combined"] = combined_file
            self.logger.info(f"Exported combined results: {combined_file}")
        
        return exported_files
    
    def print_results_summary(self, results: Dict[str, List[JobDescription]]):
        """Print summary of crawling results"""
        print("\n" + "="*60)
        print("CRAWLING RESULTS SUMMARY")
        print("="*60)
        
        total_jobs = 0
        for category, jobs in results.items():
            print(f"{category:25} | {len(jobs):4} jobs")
            total_jobs += len(jobs)
        
        print("-"*60)
        print(f"{'TOTAL':25} | {total_jobs:4} jobs")
        print("="*60)
        
        # Show sample job for each category
        print("\nSAMPLE JOBS:")
        for category, jobs in results.items():
            if jobs:
                job = jobs[0]
                print(f"{category}: {job.title} at {job.company}")
    
    async def run_crawl(self, categories: List[str], location: str = "Vietnam", 
                       limit_per_category: int = 25, export_format: str = "json", 
                       export_summary: bool = True) -> Dict[str, str]:
        """Main crawl execution method"""
        self.logger.info("Starting JD Crawler execution")
        
        # Crawl jobs
        results = await self.crawl_categories(categories, location, limit_per_category)
        
        if not results:
            self.logger.warning("No results to export")
            return {}
        
        # Export results
        exported_files = self.export_results(results, export_format, export_summary)
        
        # Print summary
        self.print_results_summary(results)
        
        # Print exported files
        print("\nEXPORTED FILES:")
        for category, filepath in exported_files.items():
            print(f"  {category}: {filepath}")
        
        self.logger.info("JD Crawler execution completed")
        return exported_files


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Job Description Crawler - Crawl job listings from various sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m crawling --categories ACCOUNTANT ENGINEERING --limit 50
  python -m crawling --all-categories --location "Hà Nội" --format csv
  python -m crawling --categories IT --limit 100 --no-summary
        """
    )
    
    # Category selection
    category_group = parser.add_mutually_exclusive_group(required=True)
    category_group.add_argument(
        '--categories', 
        nargs='+', 
        help='List of categories to crawl (e.g., ACCOUNTANT ENGINEERING IT)'
    )
    category_group.add_argument(
        '--all-categories',
        action='store_true',
        help='Crawl all available categories'
    )
    
    # Crawl parameters
    parser.add_argument(
        '--location',
        default='Vietnam',
        help='Location to search for jobs (default: Vietnam)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=25,
        help='Limit per category (default: 25)'
    )
    parser.add_argument(
        '--mcp-server',
        default='playwright',
        help='MCP server name (default: playwright)'
    )
    
    # Export options
    parser.add_argument(
        '--format',
        choices=['json', 'csv', 'api'],
        default='json',
        help='Export format (default: json)'
    )
    parser.add_argument(
        '--output-dir',
        default='output',
        help='Output directory (default: output)'
    )
    parser.add_argument(
        '--no-summary',
        action='store_true',
        help='Skip summary export'
    )
    
    # Debug options
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize orchestrator
    orchestrator = JDCCrawlerOrchestrator(
        output_dir=args.output_dir,
        mcp_server=args.mcp_server
    )
    
    # Determine categories to crawl
    if args.all_categories:
        categories = orchestrator.get_available_categories()
        print(f"Crawling all {len(categories)} categories...")
    else:
        categories = args.categories
    
    # Run crawl
    try:
        results = asyncio.run(orchestrator.run_crawl(
            categories=categories,
            location=args.location,
            limit_per_category=args.limit,
            export_format=args.format,
            export_summary=not args.no_summary
        ))
        
        if results:
            print(f"\n✅ Crawl completed successfully!")
            print(f"📁 Results exported to: {args.output_dir}")
        else:
            print("\n❌ No results to export")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Crawl interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Crawl failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()