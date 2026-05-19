// drill.js — Spaced repetition drill logic

document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-drill');
    const drillArea = document.getElementById('drill-area');
    const drillStats = document.getElementById('drill-stats');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const cardText = document.getElementById('card-text');
    const cardTranslation = document.getElementById('card-translation');
    const cardFront = document.getElementById('card-front');
    const cardBack = document.getElementById('card-back');
    const playAudioBtn = document.getElementById('play-audio');
    const showAnswerBtn = document.getElementById('show-answer');
    const reviewButtons = document.querySelectorAll('.review-buttons .btn');

    let currentCardIndex = 0;
    let cards = [];
    let session = null;
    let correctCount = 0;
    let totalReviews = 0;

    startBtn.addEventListener('click', async () => {
        const mode = document.getElementById('drill-mode').value;
        const limit = parseInt(document.getElementById('drill-limit').value);

        // Create session
        const sessionRes = await fetch('/api/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: `Drill Session - ${new Date().toLocaleString()}`,
                description: `Mode: ${mode}, Limit: ${limit}`,
            }),
        });
        const sessionData = await sessionRes.json();
        session = sessionData;

        // Get due cards
        const clipsRes = await fetch('/api/clips');
        const allClips = await clipsRes.json();

        // Filter due cards
        const now = new Date().toISOString();
        cards = allClips
            .filter(c => !c.next_due || c.next_due <= now)
            .sort((a, b) => (a.next_due || '').localeCompare(b.next_due || ''))
            .slice(0, limit);

        if (cards.length === 0) {
            alert('No cards due for review. Try again later!');
            return;
        }

        currentCardIndex = 0;
        correctCount = 0;
        totalReviews = 0;

        drillArea.style.display = 'block';
        drillStats.style.display = 'none';
        showCard();
    });

    function showCard() {
        if (currentCardIndex >= cards.length) {
            drillArea.style.display = 'none';
            drillStats.style.display = 'block';
            document.getElementById('drill-summary').textContent =
                `You reviewed ${totalReviews} cards. ${correctCount} correct.`;
            return;
        }

        const card = cards[currentCardIndex];
        const mode = document.getElementById('drill-mode').value;

        // Set card content based on mode
        if (mode === 'translate' || mode === 'mixed') {
            cardText.textContent = card.source_text || card.target_text;
            cardTranslation.textContent = card.target_text || card.source_text;
        } else if (mode === 'reverse') {
            cardText.textContent = card.target_text || card.source_text;
            cardTranslation.textContent = card.source_text || card.target_text;
        } else if (mode === 'shadow') {
            cardText.textContent = card.source_text || card.target_text;
            cardTranslation.textContent = card.target_text || card.source_text;
        }

        // Reset card state
        cardFront.style.display = 'flex';
        cardBack.style.display = 'none';
        cardTranslation.parentElement.style.display = 'none';

        // Update progress
        const pct = ((currentCardIndex) / cards.length) * 100;
        progressFill.style.width = pct + '%';
        progressText.textContent = `Card ${currentCardIndex + 1} of ${cards.length}`;
    }

    showAnswerBtn.addEventListener('click', () => {
        cardFront.style.display = 'none';
        cardBack.style.display = 'block';
        cardTranslation.parentElement.style.display = 'block';
    });

    playAudioBtn.addEventListener('click', () => {
        const card = cards[currentCardIndex];
        const text = card.source_text || card.target_text;
        const utterance = new SpeechSynthesisUtterance(text);
        speechSynthesis.speak(utterance);
    });

    reviewButtons.forEach(btn => {
        btn.addEventListener('click', async () => {
            const quality = parseInt(btn.dataset.quality);
            const card = cards[currentCardIndex];

            // Record review
            try {
                await fetch(`/api/review/${card.clip_id}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        quality: quality,
                        session_id: session.session_id,
                    }),
                });
            } catch (err) {
                console.error('Review save error:', err);
            }

            totalReviews++;
            if (quality >= 3) correctCount++;

            currentCardIndex++;
            showCard();
        });
    });
});
