import logging
from datetime import datetime, timedelta
from celery import shared_task
from sqlalchemy import func

from app.database import SessionLocal
from app.models.review import Review
from app.models.business_profile import BusinessProfile
from app.services.email_sender import email_sender

logger = logging.getLogger(__name__)

@shared_task(name="tasks.send_daily_digest")
def send_daily_digest():
    """Generates and sends a daily digest of reviews for all businesses."""
    db = SessionLocal()
    try:
        businesses = db.query(BusinessProfile).all()
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        for biz in businesses:
            if not biz.contact_email:
                continue
                
            # Get reviews from the last 24 hours
            recent_reviews = db.query(Review).filter(
                Review.business_id == str(biz.id),
                Review.created_at >= yesterday
            ).all()
            
            if not recent_reviews:
                continue
                
            avg_sentiment = sum(r.sentiment_score for r in recent_reviews if r.sentiment_score is not None) / len(recent_reviews)
            
            html_content = f"""
            <html>
                <body>
                    <h2>Daily Review Digest for {biz.name}</h2>
                    <p>You received {len(recent_reviews)} new reviews yesterday.</p>
                    <p>Average Sentiment Score: {avg_sentiment:.2f}</p>
                    <ul>
            """
            for r in recent_reviews[:5]:
                html_content += f"<li>[{r.platform}] {r.rating} stars: {r.text[:50]}...</li>"
            html_content += """
                    </ul>
                    <p>Log in to your dashboard to view more and respond.</p>
                </body>
            </html>
            """
            
            email_sender.send_digest(biz.contact_email, f"Daily Review Digest - {biz.name}", html_content)
            
    except Exception as e:
        logger.error(f"Failed to send daily digest: {e}")
    finally:
        db.close()
