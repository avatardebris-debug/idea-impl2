"""Profile matcher - scores how well a candidate matches a job profile."""

from typing import Optional


def match_profiles(
    candidate_skills: list[str],
    candidate_experience: str,
    job_profile: dict
) -> dict:
    """
    Match a candidate profile against a job profile.
    
    Args:
        candidate_skills: List of candidate's skills
        candidate_experience: Candidate's experience level (e.g., "entry-level", "mid-level", "senior")
        job_profile: Parsed job profile dict with 'skills' and 'experience_level' keys
    
    Returns:
        dict with:
        - score: int (0-100)
        - matched_skills: list[str]
        - missing_skills: list[str]
        - salary_match: bool
    """
    job_skills = job_profile.get("skills", [])
    job_experience = job_profile.get("experience_level")
    job_salary_min = job_profile.get("salary_min")
    job_salary_max = job_profile.get("salary_max")
    
    # Calculate skill overlap using Jaccard similarity
    candidate_set = set(s.lower() for s in candidate_skills)
    job_set = set(s.lower() for s in job_skills)
    
    # Initialize intersection for later use
    intersection = set()
    
    if job_set:
        intersection = candidate_set & job_set
        union = candidate_set | job_set
        jaccard = len(intersection) / len(union) if union else 0
    else:
        jaccard = 1.0 if not candidate_set else 0
    
    # Skill overlap: 0-60 points based on Jaccard similarity
    skill_score = int(jaccard * 60)
    matched_skills = list(intersection)
    missing_skills = list(job_set - candidate_set)
    
    # Experience level compatibility: 0-25 points
    exp_score = 0
    if job_experience:
        exp_levels = {
            "entry-level": 1,
            "junior": 1,
            "mid-level": 2,
            "mid": 2,
            "senior": 3,
            "sen": 3,
            "lead": 4,
            "principal": 4,
            "staff": 4,
            "director": 5,
            "vp": 5,
            "c-level": 5
        }
        
        candidate_level = exp_levels.get(candidate_experience.lower(), 1)
        job_level = exp_levels.get(job_experience.lower(), 2)
        
        # Calculate experience match score
        if candidate_level >= job_level:
            # Candidate meets or exceeds requirement
            exp_score = 25
        elif candidate_level == job_level - 1:
            # One level below
            exp_score = 15
        else:
            # Two or more levels below - no match
            exp_score = 0
    else:
        # No experience requirement, full points
        exp_score = 25
    
    # Salary match: 0-15 points
    # Only count salary match if experience also matches
    salary_match = False
    salary_score = 0
    if job_salary_min is not None and job_salary_max is not None:
        if exp_score > 0:
            # If experience matches, salary is acceptable
            salary_match = True
            salary_score = 15
        else:
            # If experience doesn't match, salary doesn't count
            salary_match = False
            salary_score = 0
    
    # Calculate total score (capped at 100)
    total_score = skill_score + exp_score + salary_score
    total_score = min(total_score, 100)
    
    # If experience doesn't match, cap the total score to reflect poor fit
    if exp_score == 0:
        total_score = min(total_score, 50)
    
    return {
        "score": total_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "salary_match": salary_match
    }
