"""SEO scoring engine — evaluates an SEOReport against best practices."""

from __future__ import annotations

from seo_tool.models import SEOReport


class Scorer:
    """Scores an SEOReport on a 0-100 scale with category breakdowns.

    Category weights (must sum to 100):
        title             10
        meta_description  10
        headings           5
        images             5
        links              5
        content_length    30
        og_tags           10
        canonical         10
        h1_count          15
    """

    WEIGHTS: dict[str, int] = {
        "title": 10,
        "meta_description": 10,
        "headings": 5,
        "images": 5,
        "links": 5,
        "content_length": 30,
        "og_tags": 10,
        "canonical": 10,
        "h1_count": 15,
    }

    def score(self, report: SEOReport) -> dict:
        """Return scoring results for *report*.

        Returns:
            {
                "total_score": int,
                "category_scores": {name: {"score": int, "max": int, "reason": str}},
            }
        """
        category_scores: dict[str, dict] = {}

        category_scores["title"] = self._score_title(report)
        category_scores["meta_description"] = self._score_meta_description(report)
        category_scores["headings"] = self._score_headings(report)
        category_scores["images"] = self._score_images(report)
        category_scores["links"] = self._score_links(report)
        category_scores["content_length"] = self._score_content_length(report)
        category_scores["og_tags"] = self._score_og_tags(report)
        category_scores["canonical"] = self._score_canonical(report)
        category_scores["h1_count"] = self._score_h1_count(report)

        total = sum(cs["score"] for cs in category_scores.values())
        total = min(total, 100)  # cap at 100

        return {
            "total_score": total,
            "category_scores": category_scores,
        }

    # -- Category scorers ------

    def _score_title(self, report: SEOReport) -> dict:
        max_w = self.WEIGHTS["title"]
        if not report.title:
            return {"score": 0, "max": max_w, "reason": "Missing title tag"}
        length = len(report.title)
        if 30 <= length <= 60:
            return {"score": max_w, "max": max_w, "reason": f"Title length OK ({length} chars)"}
        elif length < 30:
            return {"score": max_w // 2, "max": max_w, "reason": f"Title too short ({length} chars, recommend 30-60)"}
        else:
            return {"score": max_w // 2, "max": max_w, "reason": f"Title too long ({length} chars, recommend 30-60)"}

    def _score_meta_description(self, report: SEOReport) -> dict:
        max_w = self.WEIGHTS["meta_description"]
        if not report.meta_description:
            return {"score": 0, "max": max_w, "reason": "Missing meta description"}
        length = len(report.meta_description)
        if 120 <= length <= 160:
            return {"score": max_w, "max": max_w, "reason": f"Meta description length OK ({length} chars)"}
        elif length < 120:
            return {"score": max_w // 2, "max": max_w, "reason": f"Meta description too short ({length} chars, recommend 120-160)"}
        else:
            return {"score": max_w // 2, "max": max_w, "reason": f"Meta description too long ({length} chars, recommend 120-160)"}

    def _score_headings(self, report: SEOReport) -> dict:
        max_w = self.WEIGHTS["headings"]
        if not report.headings:
            return {"score": 0, "max": max_w, "reason": "No headings found"}
        # Score based on having a good mix of heading levels
        levels_present = {h[0] for h in report.headings}
        score = 0
        if 1 in levels_present:
            score += 2
        if 2 in levels_present:
            score += 1
        if 3 in levels_present:
            score += 1
        if len(report.headings) >= 3:
            score += 1
        return {"score": min(score, max_w), "max": max_w, "reason": f"Found {len(report.headings)} headings across levels {sorted(levels_present)}"}

    def _score_images(self, report: SEOReport) -> dict:
        max_w = self.WEIGHTS["images"]
        if not report.images:
            return {"score": 0, "max": max_w, "reason": "No images found"}
        with_alt = sum(1 for img in report.images if img.alt)
        score = min(with_alt, max_w)
        return {"score": score, "max": max_w, "reason": f"{with_alt}/{len(report.images)} images have alt text"}

    def _score_links(self, report: SEOReport) -> dict:
        max_w = self.WEIGHTS["links"]
        if report.link_count == 0:
            return {"score": 0, "max": max_w, "reason": "No links found"}
        internal = len(report.internal_links)
        external = len(report.external_links)
        # Full marks if both internal and external links are present
        if internal > 0 and external > 0:
            return {"score": max_w, "max": max_w, "reason": f"{internal} internal, {external} external links"}
        # Partial marks for having at least some links
        if internal > 0 or external > 0:
            return {"score": max_w // 2, "max": max_w, "reason": f"{internal} internal, {external} external links"}
        return {"score": 0, "max": max_w, "reason": "No links found"}

    def _score_content_length(self, report: SEOReport) -> dict:
        max_w = self.WEIGHTS["content_length"]
        wc = report.word_count
        if wc >= 300:
            return {"score": max_w, "max": max_w, "reason": f"Content length OK ({wc} words)"}
        elif wc >= 100:
            return {"score": max_w // 2, "max": max_w, "reason": f"Content somewhat thin ({wc} words, recommend 300+)"}
        else:
            return {"score": 0, "max": max_w, "reason": f"Content too thin ({wc} words, recommend 300+)"}

    def _score_og_tags(self, report: SEOReport) -> dict:
        max_w = self.WEIGHTS["og_tags"]
        if not report.og_tags:
            return {"score": 0, "max": max_w, "reason": "No Open Graph tags found"}
        og_props = {t.property for t in report.og_tags}
        score = 0
        if "og:title" in og_props:
            score += 4
        if "og:description" in og_props:
            score += 4
        if "og:image" in og_props:
            score += 2
        return {"score": min(score, max_w), "max": max_w, "reason": f"OG tags: {', '.join(sorted(og_props))}"}

    def _score_canonical(self, report: SEOReport) -> dict:
        max_w = self.WEIGHTS["canonical"]
        if report.canonical_link:
            return {"score": max_w, "max": max_w, "reason": "Canonical link present"}
        return {"score": 0, "max": max_w, "reason": "Missing canonical link"}

    def _score_h1_count(self, report: SEOReport) -> dict:
        max_w = self.WEIGHTS["h1_count"]
        h1s = [h for h in report.headings if h[0] == 1]
        count = len(h1s)
        if count == 1:
            return {"score": max_w, "max": max_w, "reason": f"Exactly 1 H1 tag (ideal)"}
        elif count == 0:
            return {"score": 0, "max": max_w, "reason": "No H1 tag found"}
        else:
            return {"score": max_w // 2, "max": max_w, "reason": f"Multiple H1 tags ({count}, recommend 1)"}
