"""
Export utilities for job description data

Provides various export formats for crawled job descriptions including JSON, CSV,
and database integration.
"""

import json
import csv
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from src.models import JobDescription


class JobDescriptionExporter:
    """Export job descriptions to various formats"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def export_to_json(self, jobs: List[JobDescription], filename: Optional[str] = None) -> str:
        """Export jobs to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"job_descriptions_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # Convert jobs to dictionary format
            jobs_data = [job.to_dict() for job in jobs]
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(jobs_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Successfully exported {len(jobs)} jobs to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error exporting to JSON: {str(e)}")
            raise
    
    def export_to_csv(self, jobs: List[JobDescription], filename: Optional[str] = None) -> str:
        """Export jobs to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"job_descriptions_{timestamp}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                # Define CSV headers
                fieldnames = [
                    'title', 'company', 'location', 'category', 'job_type', 
                    'experience_level', 'salary_min', 'salary_max', 'currency',
                    'description', 'requirements', 'benefits', 'skills_required', 
                    'skills_nice_to_have', 'source', 'url', 'posted_date', 'crawled_at'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for job in jobs:
                    row = {
                        'title': job.title,
                        'company': job.company,
                        'location': job.location,
                        'category': job.category,
                        'job_type': job.job_type,
                        'experience_level': job.experience_level,
                        'salary_min': job.salary_min,
                        'salary_max': job.salary_max,
                        'currency': job.currency,
                        'description': job.description,
                        'requirements': '; '.join(job.requirements),
                        'benefits': '; '.join(job.benefits),
                        'skills_required': '; '.join(job.skills_required),
                        'skills_nice_to_have': '; '.join(job.skills_nice_to_have),
                        'source': job.source,
                        'url': job.url,
                        'posted_date': job.posted_date.isoformat() if job.posted_date else '',
                        'crawled_at': job.crawled_at.isoformat()
                    }
                    writer.writerow(row)
            
            self.logger.info(f"Successfully exported {len(jobs)} jobs to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {str(e)}")
            raise
    
    def export_by_category(self, jobs_by_category: Dict[str, List[JobDescription]], 
                          format_type: str = "json") -> Dict[str, str]:
        """Export jobs grouped by category"""
        exported_files = {}
        
        for category, jobs in jobs_by_category.items():
            if not jobs:
                continue
            
            # Clean category name for filename
            clean_category = category.replace('-', '_').lower()
            
            if format_type.lower() == "json":
                filename = f"jobs_{clean_category}.json"
                filepath = self.export_to_json(jobs, filename)
            elif format_type.lower() == "csv":
                filename = f"jobs_{clean_category}.csv"
                filepath = self.export_to_csv(jobs, filename)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            
            exported_files[category] = filepath
        
        return exported_files
    
    def export_summary_report(self, jobs_by_category: Dict[str, List[JobDescription]], 
                             filename: Optional[str] = None) -> str:
        """Export a summary report of crawled jobs"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"crawl_summary_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # Generate summary statistics
            total_jobs = sum(len(jobs) for jobs in jobs_by_category.values())
            
            summary = {
                "crawl_summary": {
                    "total_categories": len(jobs_by_category),
                    "total_jobs": total_jobs,
                    "timestamp": datetime.now().isoformat(),
                    "categories": {}
                },
                "category_breakdown": {},
                "source_breakdown": {},
                "salary_statistics": {},
                "experience_level_breakdown": {}
            }
            
            # Category breakdown
            for category, jobs in jobs_by_category.items():
                summary["category_breakdown"][category] = {
                    "job_count": len(jobs),
                    "sources": list(set(job.source for job in jobs)),
                    "average_salary_min": self._calculate_average_salary([j.salary_min for j in jobs if j.salary_min]),
                    "average_salary_max": self._calculate_average_salary([j.salary_max for j in jobs if j.salary_max])
                }
            
            # Source breakdown
            all_jobs = []
            for jobs in jobs_by_category.values():
                all_jobs.extend(jobs)
            
            source_counts = {}
            for job in all_jobs:
                source_counts[job.source] = source_counts.get(job.source, 0) + 1
            summary["source_breakdown"] = source_counts
            
            # Experience level breakdown
            experience_counts = {}
            for job in all_jobs:
                exp_level = job.experience_level or "Unknown"
                experience_counts[exp_level] = experience_counts.get(exp_level, 0) + 1
            summary["experience_level_breakdown"] = experience_counts
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Successfully exported summary report to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error exporting summary report: {str(e)}")
            raise
    
    def export_for_api(self, jobs: List[JobDescription], filename: Optional[str] = None) -> str:
        """Export jobs in API-ready format"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_jobs_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # API format with pagination and metadata
            api_data = {
                "data": [job.to_dict() for job in jobs],
                "metadata": {
                    "total": len(jobs),
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(api_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Successfully exported {len(jobs)} jobs in API format to {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error exporting API format: {str(e)}")
            raise
    
    def _calculate_average_salary(self, salaries: List[Optional[int]]) -> Optional[float]:
        """Calculate average salary from list of salary values"""
        if not salaries:
            return None
        
        valid_salaries = [s for s in salaries if s is not None]
        if not valid_salaries:
            return None
        
        return sum(valid_salaries) / len(valid_salaries)


class DatabaseExporter:
    """Export jobs to database (placeholder for future implementation)"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.logger = logging.getLogger(__name__)
    
    def export_to_database(self, jobs: List[JobDescription]):
        """Export jobs to database (to be implemented)"""
        # This would contain database connection and insertion logic
        # For now, just log the operation
        self.logger.info(f"Would export {len(jobs)} jobs to database: {self.connection_string}")
        
        # Example structure for future implementation:
        # 1. Connect to database
        # 2. Create tables if they don't exist
        # 3. Insert jobs data
        # 4. Handle duplicates and updates
        # 5. Commit and close connection
        
        raise NotImplementedError("Database export not yet implemented")


# Convenience functions for common export operations
def export_jobs_to_json(jobs: List[JobDescription], output_dir: str = "output") -> str:
    """Quick export to JSON"""
    exporter = JobDescriptionExporter(output_dir)
    return exporter.export_to_json(jobs)


def export_jobs_to_csv(jobs: List[JobDescription], output_dir: str = "output") -> str:
    """Quick export to CSV"""
    exporter = JobDescriptionExporter(output_dir)
    return exporter.export_to_csv(jobs)


def export_jobs_by_category(jobs_by_category: Dict[str, List[JobDescription]], 
                           output_dir: str = "output", format_type: str = "json") -> Dict[str, str]:
    """Quick export by category"""
    exporter = JobDescriptionExporter(output_dir)
    return exporter.export_by_category(jobs_by_category, format_type)


def export_summary(jobs_by_category: Dict[str, List[JobDescription]], 
                  output_dir: str = "output") -> str:
    """Quick export summary report"""
    exporter = JobDescriptionExporter(output_dir)
    return exporter.export_summary_report(jobs_by_category)