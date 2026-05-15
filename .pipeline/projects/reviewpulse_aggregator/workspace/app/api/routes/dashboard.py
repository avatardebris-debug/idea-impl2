import csv
from io import StringIO
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.review import Review
from pydantic import BaseModel

router = APIRouter()

class FeedbackRequest(BaseModel):
    sentiment_feedback: str

@router.get("/export")
def export_reviews(business_id: str, db: Session = Depends(get_db)):
    """Export reviews for a business to CSV."""
    reviews = db.query(Review).filter(Review.business_id == business_id).all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "platform", "author", "rating", "text", 
        "published_at", "sentiment_score", "sentiment_label"
    ])
    
    for r in reviews:
        writer.writerow([
            r.id, r.platform, r.author, r.rating, r.text,
            r.published_at.isoformat() if r.published_at else "", 
            r.sentiment_score, r.sentiment_label
        ])
    
    output.seek(0)
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=reviews_{business_id}.csv"
    return response

@router.post("/reviews/{review_id}/feedback")
def submit_feedback(review_id: int, feedback: FeedbackRequest, db: Session = Depends(get_db)):
    """Submit feedback for misclassified sentiment."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
        
    review.sentiment_feedback = feedback.sentiment_feedback
    db.commit()
    return {"status": "success", "message": "Feedback recorded."}
