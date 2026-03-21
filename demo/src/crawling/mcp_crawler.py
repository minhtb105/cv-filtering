"""
MCP-based Job Description Crawler

Uses MCP server to interact with job boards and extract structured job data.
Provides browser automation for web crawling with Playwright integration.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import time

from src.crawling.models import JobDescription, JobSearchQuery
from src.crawling.validators import JobDescriptionValidator


class MCPCrawler:
    """
    MCP-based crawler for job descriptions
    
    Uses MCP server to automate browser interactions and extract job data
    from various job board websites.
    """
    
    def __init__(self, mcp_server_name: str = "playwright"):
        self.mcp_server_name = mcp_server_name
        self.validator = JobDescriptionValidator()
        self.logger = logging.getLogger(__name__)
        self.browser_session_active = False
        
        # Rate limiting
        self.request_delay = 2  # seconds between requests
        self.last_request_time = 0
    
    async def use_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute MCP tool with error handling"""
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.request_delay:
                await asyncio.sleep(self.request_delay - time_since_last)
            
            self.last_request_time = time.time()
            
            # This would be replaced with actual MCP tool execution
            # For now, we'll simulate the MCP interaction
            self.logger.info(f"Executing MCP tool: {tool_name} with args: {arguments}")
            
            # Simulate MCP response (in real implementation, this would come from MCP server)
            if tool_name == "browser_navigate":
                return {"status": "success", "url": arguments.get("url")}
            elif tool_name == "browser_snapshot":
                return {"status": "success", "snapshot": "mock_snapshot_data"}
            elif tool_name == "browser_evaluate":
                return {"status": "success", "result": "mock_evaluation_result"}
            else:
                return {"status": "success", "message": f"Tool {tool_name} executed"}
                
        except Exception as e:
            self.logger.error(f"MCP tool execution failed: {str(e)}")
            raise
    
    async def ensure_browser_session(self):
        """Ensure browser session is active"""
        if not self.browser_session_active:
            try:
                await self.use_mcp_tool("browser_navigate", {"url": "about:blank"})
                self.browser_session_active = True
                self.logger.info("Browser session initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize browser session: {str(e)}")
                raise
    
    async def crawl_vietnamworks(self, query: JobSearchQuery) -> List[JobDescription]:
        """Crawl VietnamWorks job board"""
        await self.ensure_browser_session()
        
        jobs = []
        search_terms = query.get_search_terms()
        
        for keyword in search_terms:
            try:
                # Navigate to search page
                search_url = f"https://www.vietnamworks.com/tim-viec-lam/{keyword.replace(' ', '-')}-kw{keyword.replace(' ', '-')}"
                if query.location != "Vietnam":
                    search_url += f"?location={query.location}"
                
                await self.use_mcp_tool("browser_navigate", {"url": search_url})
                
                # Get page snapshot
                snapshot = await self.use_mcp_tool("browser_snapshot", {})
                
                # Extract job listings
                job_listings = await self.extract_vietnamworks_jobs(snapshot, query.category)
                jobs.extend(job_listings)
                
                if len(jobs) >= query.limit:
                    break
                    
            except Exception as e:
                self.logger.error(f"Error crawling VietnamWorks with keyword {keyword}: {str(e)}")
                continue
        
        return jobs[:query.limit]
    
    async def extract_vietnamworks_jobs(self, snapshot: Dict[str, Any], category: str) -> List[JobDescription]:
        """Extract job listings from VietnamWorks snapshot"""
        jobs = []
        
        # This would contain the actual JavaScript evaluation logic
        # to extract job data from the page snapshot
        extract_script = """
        () => {
            const jobCards = document.querySelectorAll('.job-item, .job-card, [data-job-id]');
            const jobs = [];
            
            jobCards.forEach(card => {
                const title = card.querySelector('.job-title, h3, .title')?.textContent?.trim();
                const company = card.querySelector('.company-name, .employer-name')?.textContent?.trim();
                const location = card.querySelector('.location, .job-location')?.textContent?.trim();
                const salary = card.querySelector('.salary, .job-salary')?.textContent?.trim();
                const url = card.querySelector('a')?.href;
                
                if (title && company && url) {
                    jobs.push({
                        title: title,
                        company: company,
                        location: location || '',
                        salary: salary || '',
                        url: url
                    });
                }
            });
            
            return jobs;
        }
        """
        
        try:
            evaluation_result = await self.use_mcp_tool("browser_evaluate", {
                "function": extract_script
            })
            
            raw_jobs = evaluation_result.get("result", [])
            
            for raw_job in raw_jobs:
                job = self.parse_vietnamworks_job(raw_job, category)
                if job:
                    jobs.append(job)
                    
        except Exception as e:
            self.logger.error(f"Error extracting VietnamWorks jobs: {str(e)}")
        
        return jobs
    
    def parse_vietnamworks_job(self, raw_job: Dict[str, Any], category: str) -> Optional[JobDescription]:
        """Parse raw job data from VietnamWorks into JobDescription"""
        try:
            # Extract basic fields
            title = raw_job.get('title', '')
            company = raw_job.get('company', '')
            location = raw_job.get('location', '')
            url = raw_job.get('url', '')
            
            if not all([title, company, url]):
                return None
            
            # Parse salary
            salary_result = self.validator.normalize_salary(raw_job.get('salary', ''))
            
            # Create job description
            job = JobDescription(
                title=title,
                company=company,
                location=self.validator.normalize_location(location),
                category=category,
                job_type="Full-time",  # Default for VietnamWorks
                experience_level="Entry",  # Will be extracted from description
                salary_min=salary_result['min'],
                salary_max=salary_result['max'],
                currency=salary_result['currency'],
                description="",  # Will be filled by detailed extraction
                source="VietnamWorks",
                url=url,
                posted_date=datetime.now(),
                source_specific=raw_job
            )
            
            # Normalize the job description
            normalized_job = self.validator.normalize_job_description(job)
            
            return normalized_job
            
        except Exception as e:
            self.logger.error(f"Error parsing VietnamWorks job: {str(e)}")
            return None
    
    async def crawl_careerbuilder(self, query: JobSearchQuery) -> List[JobDescription]:
        """Crawl CareerBuilder Vietnam job board"""
        await self.ensure_browser_session()
        
        jobs = []
        search_terms = query.get_search_terms()
        
        for keyword in search_terms:
            try:
                search_url = f"https://www.careerbuilder.vn/viec-lam/{keyword.replace(' ', '-')}-kwd{keyword.replace(' ', '-')}"
                if query.location != "Vietnam":
                    search_url += f"?location={query.location}"
                
                await self.use_mcp_tool("browser_navigate", {"url": search_url})
                snapshot = await self.use_mcp_tool("browser_snapshot", {})
                
                job_listings = await self.extract_careerbuilder_jobs(snapshot, query.category)
                jobs.extend(job_listings)
                
                if len(jobs) >= query.limit:
                    break
                    
            except Exception as e:
                self.logger.error(f"Error crawling CareerBuilder with keyword {keyword}: {str(e)}")
                continue
        
        return jobs[:query.limit]
    
    async def extract_careerbuilder_jobs(self, snapshot: Dict[str, Any], category: str) -> List[JobDescription]:
        """Extract job listings from CareerBuilder snapshot"""
        # Similar implementation to VietnamWorks but with CareerBuilder-specific selectors
        jobs = []
        
        extract_script = """
        () => {
            const jobCards = document.querySelectorAll('.job-item, .job-card, .job-listing');
            const jobs = [];
            
            jobCards.forEach(card => {
                const title = card.querySelector('.job-title, h2, .position')?.textContent?.trim();
                const company = card.querySelector('.company, .employer')?.textContent?.trim();
                const location = card.querySelector('.location, .job-location')?.textContent?.trim();
                const salary = card.querySelector('.salary, .job-salary')?.textContent?.trim();
                const url = card.querySelector('a')?.href;
                
                if (title && company && url) {
                    jobs.push({
                        title: title,
                        company: company,
                        location: location || '',
                        salary: salary || '',
                        url: url
                    });
                }
            });
            
            return jobs;
        }
        """
        
        try:
            evaluation_result = await self.use_mcp_tool("browser_evaluate", {
                "function": extract_script
            })
            
            raw_jobs = evaluation_result.get("result", [])
            
            for raw_job in raw_jobs:
                job = self.parse_careerbuilder_job(raw_job, category)
                if job:
                    jobs.append(job)
                    
        except Exception as e:
            self.logger.error(f"Error extracting CareerBuilder jobs: {str(e)}")
        
        return jobs
    
    def parse_careerbuilder_job(self, raw_job: Dict[str, Any], category: str) -> Optional[JobDescription]:
        """Parse raw job data from CareerBuilder into JobDescription"""
        try:
            title = raw_job.get('title', '')
            company = raw_job.get('company', '')
            location = raw_job.get('location', '')
            url = raw_job.get('url', '')
            
            if not all([title, company, url]):
                return None
            
            salary_result = self.validator.normalize_salary(raw_job.get('salary', ''))
            
            job = JobDescription(
                title=title,
                company=company,
                location=self.validator.normalize_location(location),
                category=category,
                job_type="Full-time",
                experience_level="Entry",
                salary_min=salary_result['min'],
                salary_max=salary_result['max'],
                currency=salary_result['currency'],
                description="",
                source="CareerBuilder",
                url=url,
                posted_date=datetime.now(),
                source_specific=raw_job
            )
            
            normalized_job = self.validator.normalize_job_description(job)
            return normalized_job
            
        except Exception as e:
            self.logger.error(f"Error parsing CareerBuilder job: {str(e)}")
            return None
    
    async def crawl_job_description_details(self, job: JobDescription) -> JobDescription:
        """Crawl detailed job description from job URL"""
        try:
            await self.ensure_browser_session()
            await self.use_mcp_tool("browser_navigate", {"url": job.url})
            
            # Extract detailed job information
            detail_script = """
            () => {
                const description = document.querySelector('.job-description, .description, .job-content')?.textContent?.trim();
                const requirements = document.querySelector('.requirements, .job-requirements')?.textContent?.trim();
                const benefits = document.querySelector('.benefits, .job-benefits')?.textContent?.trim();
                const experience = document.querySelector('.experience, .job-experience')?.textContent?.trim();
                const jobType = document.querySelector('.job-type, .employment-type')?.textContent?.trim();
                
                return {
                    description: description || '',
                    requirements: requirements || '',
                    benefits: benefits || '',
                    experience: experience || '',
                    jobType: jobType || ''
                };
            }
            """
            
            evaluation_result = await self.use_mcp_tool("browser_evaluate", {
                "function": detail_script
            })
            
            details = evaluation_result.get("result", {})
            
            # Update job with detailed information
            job.description = details.get('description', job.description)
            job.requirements = [details.get('requirements', '')] if details.get('requirements') else job.requirements
            job.benefits = [details.get('benefits', '')] if details.get('benefits') else job.benefits
            
            if details.get('jobType'):
                job.job_type = self.validator.normalize_job_type(details['jobType'])
            
            if details.get('experience'):
                job.experience_level = self.validator.normalize_experience_level(details['experience'])
            
            # Extract skills from description
            skills = self.validator.extract_skills_from_description(job.description)
            job.skills_required.extend(skills['required'])
            job.skills_nice_to_have.extend(skills['nice_to_have'])
            
            # Normalize the updated job
            normalized_job = self.validator.normalize_job_description(job)
            
            return normalized_job
            
        except Exception as e:
            self.logger.error(f"Error crawling job details for {job.title}: {str(e)}")
            return job
    
    async def crawl_category(self, category: str, location: str = "Vietnam", limit: int = 50) -> List[JobDescription]:
        """Crawl jobs for a specific category"""
        query = JobSearchQuery(category=category, location=location, limit=limit)
        
        self.logger.info(f"Starting crawl for category: {category}, location: {location}, limit: {limit}")
        
        all_jobs = []
        
        # Crawl different sources
        try:
            vietnamworks_jobs = await self.crawl_vietnamworks(query)
            all_jobs.extend(vietnamworks_jobs)
            self.logger.info(f"Found {len(vietnamworks_jobs)} jobs from VietnamWorks")
        except Exception as e:
            self.logger.error(f"Error crawling VietnamWorks: {str(e)}")
        
        try:
            careerbuilder_jobs = await self.crawl_careerbuilder(query)
            all_jobs.extend(careerbuilder_jobs)
            self.logger.info(f"Found {len(careerbuilder_jobs)} jobs from CareerBuilder")
        except Exception as e:
            self.logger.error(f"Error crawling CareerBuilder: {str(e)}")
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_jobs = []
        for job in all_jobs:
            if job.url not in seen_urls:
                seen_urls.add(job.url)
                unique_jobs.append(job)
        
        # Crawl detailed descriptions for top jobs
        detailed_jobs = []
        for i, job in enumerate(unique_jobs[:min(20, len(unique_jobs))]):  # Limit detailed crawling
            try:
                detailed_job = await self.crawl_job_description_details(job)
                detailed_jobs.append(detailed_job)
                self.logger.info(f"Processed detailed description for job {i+1}/{len(unique_jobs)}: {job.title}")
            except Exception as e:
                self.logger.error(f"Error getting details for {job.title}: {str(e)}")
                detailed_jobs.append(job)
        
        # Fill in remaining jobs without detailed crawling
        detailed_jobs.extend(unique_jobs[min(20, len(unique_jobs)):])
        
        # Sort by relevance and return limited results
        return detailed_jobs[:limit]
    
    async def crawl_multiple_categories(self, categories: List[str], location: str = "Vietnam", limit_per_category: int = 25) -> Dict[str, List[JobDescription]]:
        """Crawl multiple categories"""
        results = {}
        
        for category in categories:
            try:
                jobs = await self.crawl_category(category, location, limit_per_category)
                results[category] = jobs
                self.logger.info(f"Completed crawl for {category}: {len(jobs)} jobs found")
            except Exception as e:
                self.logger.error(f"Error crawling category {category}: {str(e)}")
                results[category] = []
        
        return results
    
    async def close(self):
        """Clean up browser session"""
        try:
            if self.browser_session_active:
                await self.use_mcp_tool("browser_close", {})
                self.browser_session_active = False
                self.logger.info("Browser session closed")
        except Exception as e:
            self.logger.error(f"Error closing browser session: {str(e)}")


# Convenience function for easy usage
async def crawl_jobs(categories: List[str], location: str = "Vietnam", limit_per_category: int = 25, mcp_server: str = "playwright") -> Dict[str, List[JobDescription]]:
    """Convenience function to crawl jobs from multiple categories"""
    crawler = MCPCrawler(mcp_server)
    
    try:
        results = await crawler.crawl_multiple_categories(categories, location, limit_per_category)
        return results
    finally:
        await crawler.close()