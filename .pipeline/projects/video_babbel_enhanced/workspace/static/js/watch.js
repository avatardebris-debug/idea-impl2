// watch.js — Watch page logic

document.addEventListener('DOMContentLoaded', () => {
    const clipId = window.location.pathname.split('/watch/')[1];
    const videoPlayer = document.getElementById('video-player');
    const clipTitle = document.getElementById('clip-title');
    const clipTranscript = document.getElementById('clip-transcript');
    const clipTranslation = document.getElementById('clip-translation');
    const clipFreq = document.getElementById('clip-freq');
    const stars = document.querySelectorAll('#stars span');
    const reviewStatus = document.getElementById('review-status');
    const lipsyncBtn = document.getElementById('lipsync-btn');
    const lipsyncResult = document.getElementById('lipsync-result');
    const lipsyncVideo = document.getElementById('lipsync-video');

    // Load clip data
    loadClip();

    async function loadClip() {
        try {
            const res = await fetch('/api/clips');
            const clips = await res.json();
            const clip = clips.find(c => c.clip_id === clipId);
            if (!clip) {
                clipTitle.textContent = 'Clip not found';
                return;
            }

            clipTitle.textContent = clip.source_text || 'Clip';
            clipTranscript.textContent = `📝 ${clip.source_text || 'No transcript'}`;
            clipTranslation.textContent = `🌐 ${clip.target_text || 'No translation'}`;
            clipFreq.textContent = `📊 Frequency Score: ${clip.frequency_score || 0}`;

            // Set video source
            if (clip.clip_path) {
                videoPlayer.querySelector('source').src = clip.clip_path;
                videoPlayer.load();
            }
        } catch (err) {
            clipTitle.textContent = 'Error loading clip';
        }
    }

    // Star rating
    let selectedQuality = 0;
    stars.forEach(star => {
        star.addEventListener('click', async () => {
            selectedQuality = parseInt(star.dataset.quality);
            updateStars(selectedQuality);
            reviewStatus.textContent = 'Saving rating...';

            try {
                const res = await fetch(`/api/review/${clipId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ quality: selectedQuality }),
                });
                const data = await res.json();
                if (data.status) {
                    reviewStatus.textContent = 'Rating saved!';
                } else {
                    reviewStatus.textContent = 'Error saving rating';
                }
            } catch (err) {
                reviewStatus.textContent = 'Error: ' + err.message;
            }
        });

        star.addEventListener('mouseenter', () => {
            updateStars(parseInt(star.dataset.quality));
        });
    });

    function updateStars(quality) {
        stars.forEach(s => {
            s.classList.toggle('active', parseInt(s.dataset.quality) <= quality);
            s.textContent = parseInt(s.dataset.quality) <= quality ? '★' : '☆';
        });
    }

    // Lip sync
    lipsyncBtn.addEventListener('click', async () => {
        lipsyncBtn.disabled = true;
        lipsyncBtn.textContent = 'Generating...';
        lipsyncResult.style.display = 'none';

        try {
            const res = await fetch(`/api/lipsync/${clipId}`, {
                method: 'POST',
            });
            const data = await res.json();
            if (data.status) {
                lipsyncResult.style.display = 'block';
                lipsyncVideo.querySelector('source').src = `/clips/${clipId}_lipsync.mp4`;
                lipsyncVideo.load();
                lipsyncBtn.textContent = 'Regenerate';
            } else {
                alert('Lip sync error: ' + data.error);
                lipsyncBtn.disabled = false;
                lipsyncBtn.textContent = 'Generate Lip Sync';
            }
        } catch (err) {
            alert('Error: ' + err.message);
            lipsyncBtn.disabled = false;
            lipsyncBtn.textContent = 'Generate Lip Sync';
        }
    });
});
