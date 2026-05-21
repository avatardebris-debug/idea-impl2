"""Sample reviews for MVP testing. Contains realistic mock reviews with gap-indicating phrases."""

from book_researcher.models import BookReview


def get_sample_reviews() -> list[BookReview]:
    """Return a list of sample BookReview objects with gap-indicating content."""
    return [
        # Book: "Deep Learning Fundamentals" (book_id: dl_fundamentals)
        BookReview(
            book_id="dl_fundamentals",
            text="Great overview of neural networks, but I wish it also covered transfer learning in depth. The chapter on it was too brief.",
            rating=4.0,
            source="goodreads",
            reviewer="Alice M.",
        ),
        BookReview(
            book_id="dl_fundamentals",
            text="The math is solid, but it didn't explain how to handle imbalanced datasets in practice. That's a huge gap for real-world applications.",
            rating=3.5,
            source="amazon",
            reviewer="Bob K.",
        ),
        BookReview(
            book_id="dl_fundamentals",
            text="I wanted more on model deployment and serving. The book stops at training and evaluation, which leaves a big hole for practitioners.",
            rating=3.0,
            source="goodreads",
            reviewer="Carol S.",
        ),
        BookReview(
            book_id="dl_fundamentals",
            text="Missing coverage of reinforcement learning entirely. For a deep learning book, that's a glaring omission.",
            rating=3.5,
            source="amazon",
            reviewer="Dan R.",
        ),
        BookReview(
            book_id="dl_fundamentals",
            text="Should have covered attention mechanisms and transformers more thoroughly. The brief mention wasn't enough.",
            rating=4.0,
            source="goodreads",
            reviewer="Eve T.",
        ),
        BookReview(
            book_id="dl_fundamentals",
            text="I wish the author had explained how to debug neural networks. No section on debugging or troubleshooting.",
            rating=3.0,
            source="amazon",
            reviewer="Frank W.",
        ),
        BookReview(
            book_id="dl_fundamentals",
            text="Lacks practical examples with modern frameworks like PyTorch. Only TensorFlow examples, which is limiting.",
            rating=3.5,
            source="goodreads",
            reviewer="Grace L.",
        ),
        BookReview(
            book_id="dl_fundamentals",
            text="Didn't explain how to optimize for GPU vs CPU. Important for anyone working with large models.",
            rating=4.0,
            source="amazon",
            reviewer="Hank P.",
        ),
        BookReview(
            book_id="dl_fundamentals",
            text="The book is good but I wish it also covered ethical considerations in AI. That's increasingly important.",
            rating=3.5,
            source="goodreads",
            reviewer="Ivy N.",
        ),
        BookReview(
            book_id="dl_fundamentals",
            text="Missing a section on data augmentation techniques. That's essential for any deep learning practitioner.",
            rating=3.0,
            source="amazon",
            reviewer="Jack B.",
        ),

        # Book: "Machine Learning Engineering" (book_id: ml_eng)
        BookReview(
            book_id="ml_eng",
            text="Good on MLOps basics, but I wish it also covered model versioning and experiment tracking tools like MLflow.",
            rating=4.0,
            source="goodreads",
            reviewer="Karen D.",
        ),
        BookReview(
            book_id="ml_eng",
            text="It didn't explain how to handle data drift in production. That's a critical gap for anyone deploying models.",
            rating=3.5,
            source="amazon",
            reviewer="Leo F.",
        ),
        BookReview(
            book_id="ml_eng",
            text="Lacks coverage of feature stores. For a book on ML engineering, that's a significant omission.",
            rating=3.0,
            source="goodreads",
            reviewer="Mia G.",
        ),
        BookReview(
            book_id="ml_eng",
            text="Should have covered A/B testing for ML models. The book only discusses traditional A/B testing.",
            rating=4.0,
            source="amazon",
            reviewer="Noah H.",
        ),
        BookReview(
            book_id="ml_eng",
            text="I want more on model compression and quantization for edge deployment. That's missing entirely.",
            rating=3.5,
            source="goodreads",
            reviewer="Olivia J.",
        ),
        BookReview(
            book_id="ml_eng",
            text="Missing discussion of model monitoring and alerting. How do you know when a model degrades?",
            rating=3.0,
            source="amazon",
            reviewer="Paul K.",
        ),
        BookReview(
            book_id="ml_eng",
            text="Didn't explain how to build CI/CD pipelines for ML. The DevOps section is too generic.",
            rating=4.0,
            source="goodreads",
            reviewer="Quinn L.",
        ),
        BookReview(
            book_id="ml_eng",
            text="The book lacks coverage of federated learning. That's becoming increasingly relevant for privacy.",
            rating=3.5,
            source="amazon",
            reviewer="Rachel M.",
        ),
        BookReview(
            book_id="ml_eng",
            text="I wish it also covered autoML tools. For practitioners, that's a huge time-saver.",
            rating=3.0,
            source="goodreads",
            reviewer="Sam N.",
        ),
        BookReview(
            book_id="ml_eng",
            text="Should have covered model fairness and bias detection. That's a must-have for responsible ML.",
            rating=4.0,
            source="amazon",
            reviewer="Tina O.",
        ),

        # Book: "Natural Language Processing" (book_id: nlp_book)
        BookReview(
            book_id="nlp_book",
            text="Great on classical NLP, but I wish it also covered transformer architectures in depth. The attention section was too shallow.",
            rating=4.0,
            source="goodreads",
            reviewer="Uma P.",
        ),
        BookReview(
            book_id="nlp_book",
            text="It didn't explain how to fine-tune pre-trained models like BERT. That's the most practical skill needed today.",
            rating=3.5,
            source="amazon",
            reviewer="Victor Q.",
        ),
        BookReview(
            book_id="nlp_book",
            text="Lacks coverage of text generation and large language models. For a modern NLP book, that's a glaring gap.",
            rating=3.0,
            source="goodreads",
            reviewer="Wendy R.",
        ),
        BookReview(
            book_id="nlp_book",
            text="Missing a section on multilingual NLP. The book only covers English, which limits its usefulness.",
            rating=3.5,
            source="amazon",
            reviewer="Xander S.",
        ),
        BookReview(
            book_id="nlp_book",
            text="Should have covered named entity recognition in more detail. The examples were too simplistic.",
            rating=4.0,
            source="goodreads",
            reviewer="Yara T.",
        ),
        BookReview(
            book_id="nlp_book",
            text="I want more on sentiment analysis with aspect-based approaches. The book only covers document-level sentiment.",
            rating=3.0,
            source="amazon",
            reviewer="Zack U.",
        ),
        BookReview(
            book_id="nlp_book",
            text="Didn't explain how to handle text preprocessing at scale. That's a practical gap for real projects.",
            rating=3.5,
            source="goodreads",
            reviewer="Amy V.",
        ),
        BookReview(
            book_id="nlp_book",
            text="The book lacks coverage of dialogue systems and chatbots. That's a huge area of NLP.",
            rating=3.0,
            source="amazon",
            reviewer="Brian W.",
        ),
        BookReview(
            book_id="nlp_book",
            text="I wish it also covered prompt engineering for LLMs. That's the new frontier in NLP.",
            rating=4.0,
            source="goodreads",
            reviewer="Cindy X.",
        ),
        BookReview(
            book_id="nlp_book",
            text="Missing discussion of evaluation metrics for generative models. BLEU and ROUGE aren't enough anymore.",
            rating=3.5,
            source="amazon",
            reviewer="Derek Y.",
        ),
    ]
