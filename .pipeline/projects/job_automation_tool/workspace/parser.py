"""Job description parser - extracts structured fields from raw text."""

import re
from typing import Optional


def parse_job_description(text: str) -> Optional[dict]:
    """
    Parse a job description text and extract structured fields.
    
    Returns a dict with keys:
    - title: str
    - company: str
    - skills: list[str]
    - experience_level: str or None
    - salary_min: int or None
    - salary_max: int or None
    - location: str or None
    - responsibilities: list[str]
    
    Returns None if input is empty or cannot be parsed.
    """
    if not text or not text.strip():
        return None
    
    lines = text.strip().split("\n")
    
    # Extract title (first non-empty line, typically uppercase or title case)
    title = None
    for line in lines:
        line = line.strip()
        if line:
            title = line
            break
    
    # Extract company (look for patterns like "Company:", "at Company", etc.)
    company = None
    company_patterns = [
        r"(?:company|organization|employer)[:\s]+([^\n]+)",
        r"(?:at|working\s+at|working\s+for)\s+([A-Za-z][A-Za-z\s&]+?)(?:\s+(?:in|at|for|on|with))",
    ]
    for pattern in company_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            break
    
    # If no company found, try to find company name after title (second line)
    if not company and len(lines) >= 2:
        second_line = lines[1].strip()
        if second_line and not second_line.startswith(('-', '*', '•')):
            # Check if it looks like a company name (not a section header)
            if not re.match(r'^[A-Z][a-z]+:', second_line):
                company = second_line
    
    # Extract skills from bullet points under requirements
    skills = []
    # Common words to exclude when extracting skills from bullet points
    exclude_words = {'must', 'have', 'experience', 'with', 'knowledge', 'of', 'in', 'strong', 'proficiency', 'excellent', 'good', 'basic', 'familiarity', 'understanding', 'required', 'requireds'}
    requirements_section = re.search(r'requirements[\s\S]*?(?=\n\n|\n\s*\n|$)', text, re.IGNORECASE)
    if requirements_section:
        req_text = requirements_section.group(0)
        # Extract bullet points
        bullet_skills = re.findall(r'^[\s]*[-*•]\s*(.+)$', req_text, re.MULTILINE)
        for bullet in bullet_skills:
            # Extract skill names from bullet points like "Must have Python" or "JavaScript experience required"
            # Try patterns in order of specificity - more specific patterns first
            skill = None
            
            # Pattern: skill before "experience required"
            skill_match = re.search(r'([A-Z][a-zA-Z]+)\s+experience\s+required', bullet, re.IGNORECASE)
            if skill_match:
                skill = skill_match.group(1).strip()
            # Pattern: skill before "knowledge"
            elif re.search(r'([A-Z][a-zA-Z]+)\s+knowledge', bullet, re.IGNORECASE):
                skill_match = re.search(r'([A-Z][a-zA-Z]+)\s+knowledge', bullet, re.IGNORECASE)
                skill = skill_match.group(1).strip()
            # Pattern: skill after "must have" or "have"
            elif re.search(r'(?:must\s+have|have\s+)([A-Z][a-zA-Z]+)', bullet, re.IGNORECASE):
                skill_match = re.search(r'(?:must\s+have|have\s+)([A-Z][a-zA-Z]+)', bullet, re.IGNORECASE)
                skill = skill_match.group(1).strip()
            # Pattern: skill after "required" at the end
            elif re.search(r'required\s+([A-Z][a-zA-Z]+)', bullet, re.IGNORECASE):
                skill_match = re.search(r'required\s+([A-Z][a-zA-Z]+)', bullet, re.IGNORECASE)
                skill = skill_match.group(1).strip()
            # Pattern: any capitalized word
            else:
                skill_match = re.search(r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b', bullet)
                if skill_match:
                    skill = skill_match.group(1).strip()
            
            if skill and skill.lower() not in exclude_words and skill not in skills:
                skills.append(skill)
    
    # If no skills found, try to find a skills section
    if not skills:
        skills_section = re.search(r'(?:skills|technical\s+skills|required\s+skills)[\s\S]*?(?=\n\n|\n\s*\n|$)', text, re.IGNORECASE)
        if skills_section:
            skill_text = skills_section.group(0)
            skill_matches = re.findall(r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b', skill_text)
            skills = [s.strip() for s in skill_matches if s.strip()]
    
    # Extract skills (capitalized words after "skills", "requirements", "must have")
    if not skills:
        skills_patterns = [
            r"(?:skills|requirements|qualifications|must\s+have)[:\s]+([^\n]+)",
            r"(?:skills|requirements)[:\s]*([^\n]+)",
        ]
        for pattern in skills_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                skills_text = match.group(1)
                # Extract capitalized words or common skill patterns
                skill_matches = re.findall(r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b', skills_text)
                skills.extend([s.strip() for s in skill_matches if s.strip()])
                break
    
    # Extract experience level
    experience_level = None
    exp_patterns = [
        r"(?:experience|years?\s+of\s+experience)[:\s]+(\d+)\s*\+?\s*years?",
        r"(?:entry[- ]?level|junior|mid[- ]?level|senior|lead|principal|staff|director|vp|executive)",
        r"(\d+)\s*\+?\s*years?\s+(?:of\s+)?experience",
    ]
    for pattern in exp_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Check if pattern has a capture group
            if match.lastindex and match.lastindex >= 1:
                experience_level = match.group(1).lower()
            else:
                # Pattern without capture group, use the full match
                experience_level = match.group(0).lower()
            break
    
    # Extract salary range
    salary_min = None
    salary_max = None
    salary_patterns = [
        r"\$?(\d{1,3}(?:,?\d{3})*(?:\.\d{2})?)k?\s*[-–]\s*\$?(\d{1,3}(?:,?\d{3})*(?:\.\d{2})?)k?",
        r"\$?(\d{1,3}(?:,?\d{3})*(?:\.\d{2})?)\s*[-–]\s*\$?(\d{1,3}(?:,?\d{3})*(?:\.\d{2})?)",
        r"\$?(\d{1,3}(?:,?\d{3})*(?:\.\d{2})?)\s*(?:per\s+)?year",
    ]
    for pattern in salary_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                salary_min = int(match.group(1).replace(",", ""))
                salary_max = int(match.group(2).replace(",", "")) if match.group(2) else salary_min
                
                # Handle k suffix (e.g., 80k = 80000)
                if salary_min < 1000 and salary_min >= 1:
                    salary_min *= 1000
                if salary_max < 1000 and salary_max >= 1:
                    salary_max *= 1000
            except (ValueError, AttributeError):
                pass
            break
    
    # Extract location
    location = None
    location_patterns = [
        r"(?:location|work\s+location|office)[:\s]+([^\n]+)",
        r"\b(Remote|Remote\s+First|Hybrid)\b",
        r"\b([A-Za-z\s]+,\s*[A-Z]{2})\b",
    ]
    for pattern in location_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            break
    
    # Extract responsibilities (bullet points or numbered lists)
    responsibilities = []
    responsibility_patterns = [
        r"(?:responsibilities|duties|role)[:\s]*([\s\S]*?)(?=\n\n|\n\s*\n|$)",
    ]
    for pattern in responsibility_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            resp_text = match.group(1)
            # Extract bullet points or numbered items
            resp_items = re.findall(r'^[\s]*[-*•]\s*(.+)$', resp_text, re.MULTILINE)
            if not resp_items:
                resp_items = re.findall(r'^[\s]*\d+\.\s*(.+)$', resp_text, re.MULTILINE)
            responsibilities = [r.strip() for r in resp_items if r.strip()]
            break
    
    return {
        "title": title,
        "company": company,
        "skills": skills,
        "experience_level": experience_level,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "location": location,
        "responsibilities": responsibilities,
    }
