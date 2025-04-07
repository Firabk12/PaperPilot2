from dataclasses import dataclass
from typing import List, Dict
import arxiv
from difflib import SequenceMatcher
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class ComparisonResult:
    similarity_score: float
    common_topics: List[str]
    unique_aspects: Dict[str, List[str]]
    methodology_comparison: str
    findings_comparison: str
    impact_comparison: str
    timestamp: datetime = datetime.utcnow()

class PaperComparisonCache:
    def __init__(self, max_cache_age_hours: int = 24):
        self.cache: Dict[str, ComparisonResult] = {}
        self.max_cache_age = timedelta(hours=max_cache_age_hours)

    def get_cache_key(self, papers: List[arxiv.Result]) -> str:
        """Generate a cache key from paper IDs."""
        paper_ids = sorted([str(p.entry_id) for p in papers])  # Convert to str
        return "_".join(paper_ids)

    def get(self, papers: List[arxiv.Result]) -> ComparisonResult:
        """Get cached comparison result if available and not expired."""
        key = self.get_cache_key(papers)
        if key in self.cache:
            result = self.cache[key]
            if datetime.utcnow() - result.timestamp < self.max_cache_age:
                return result
            else:
                del self.cache[key]
        return None

    def set(self, papers: List[arxiv.Result], result: ComparisonResult) -> None:
        """Cache comparison result."""
        key = self.get_cache_key(papers)
        self.cache[key] = result
        self._cleanup()

    def _cleanup(self) -> None:
        """Remove expired entries from cache."""
        current_time = datetime.utcnow()
        expired_keys = [
            key for key, result in self.cache.items()
            if current_time - result.timestamp > self.max_cache_age
        ]
        for key in expired_keys:
            del self.cache[key]

# Global cache instance
comparison_cache = PaperComparisonCache()

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts using SequenceMatcher."""
    return SequenceMatcher(None, str(text1).lower(), str(text2).lower()).ratio()

def extract_key_topics(text: str, max_topics: int = 5) -> List[str]:
    """Extract key topics from text using simple keyword extraction."""
    try:
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        words = str(text).lower().split()
        topics = list(set([w for w in words if len(w) > 4 and w not in common_words]))
        return sorted(topics, key=lambda x: str(text).lower().count(x), reverse=True)[:max_topics]
    except Exception as e:
        logger.error(f"Error extracting topics: {str(e)}")
        return []

def compare_papers(papers: List[arxiv.Result]) -> ComparisonResult:
    """Compare multiple papers and generate a structured comparison."""
    if len(papers) < 2:
        raise ValueError("Need at least 2 papers to compare")

    try:
        # Calculate similarity scores between papers
        similarity_scores = []
        for i in range(len(papers)):
            for j in range(i + 1, len(papers)):
                similarity_scores.append(
                    calculate_text_similarity(str(papers[i].summary), str(papers[j].summary))
                )
        avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0

        # Extract common topics
        all_topics = []
        for paper in papers:
            all_topics.extend(extract_key_topics(str(paper.summary)))
        common_topics = list(set([topic for topic in all_topics
                                if all(topic in extract_key_topics(str(p.summary)) for p in papers)]))

        # Analyze unique aspects
        unique_aspects = {}
        for i, paper in enumerate(papers):
            topics = extract_key_topics(str(paper.summary))
            other_topics = []
            for other_paper in papers:
                if other_paper != paper:
                    other_topics.extend(extract_key_topics(str(other_paper.summary)))
            unique = list(set(topics) - set(other_topics))
            unique_aspects[f"Paper {i+1}"] = unique

        result = ComparisonResult(
            similarity_score=float(avg_similarity),
            common_topics=common_topics,
            unique_aspects=unique_aspects,
            methodology_comparison="",  # Will be filled by Gemini AI
            findings_comparison="",     # Will be filled by Gemini AI
            impact_comparison=""        # Will be filled by Gemini AI
        )

        return result

    except Exception as e:
        logger.error(f"Error comparing papers: {str(e)}")
        raise

def generate_comparison_prompt(papers: List[arxiv.Result]) -> str:
    """Generate a prompt for Gemini AI to compare papers."""
    try:
        prompt = "Please compare the following research papers:\n\n"

        for i, paper in enumerate(papers, 1):
            prompt += f"""
            Paper {i}:
            Title: {str(paper.title)}
            Authors: {', '.join(str(author) for author in paper.authors)}
            Published: {paper.published.strftime('%Y-%m-%d')}
            Categories: {str(paper.primary_category)}
            Abstract: {str(paper.summary)}

            """

        prompt += """
        Please provide a detailed comparison covering:
        1. Methodological approaches:
           - What methods does each paper use?
           - How do their approaches differ or align?
           - What are the innovative aspects of each method?

        2. Key findings:
           - What are the main results from each paper?
           - How do the results compare or contrast?
           - What are the implications of these findings?

        3. Impact and contributions:
           - How significant are their contributions?
           - What are the potential applications?
           - How do they advance the field?

        4. Strengths and limitations:
           - What are the relative strengths of each paper?
           - What are the limitations or potential weaknesses?
           - What future work do they suggest?

        Format the response in clear sections with bullet points.
        Keep the total response length under 4000 characters.
        Focus on the most important aspects if there are many to discuss.
        """

        return prompt

    except Exception as e:
        logger.error(f"Error generating prompt: {str(e)}")
        raise