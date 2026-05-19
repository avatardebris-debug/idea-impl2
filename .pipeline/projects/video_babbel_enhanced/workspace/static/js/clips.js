// clips.js — Clips listing page logic

document.addEventListener('DOMContentLoaded', () => {
    const clipsList = document.getElementById('clips-list');
    const exportBtn = document.getElementById('export-btn');

    loadClips();

    async function loadClips() {
        try {
            const res = await fetch('/api/clips');
            const clips = await res.json();
            clipsList.innerHTML = '';

            if (clips.length === 0) {
                clipsList.innerHTML = '<p class="loading">No clips yet. Upload a video first!</p>';
                return;
            }

            clips.forEach(clip => {
                const card = document.createElement('div');
                card.className = 'clip-card';
                card.innerHTML = `
                    <h3>${clip.source_text || 'Clip'}</h3>
                    <p>📝 ${clip.target_text || 'No translation'}</p>
                    <p>📊 Frequency: <span class="freq">${clip.frequency_score || 0}</span></p>
                    <p>📅 Due: ${clip.next_due || 'Never'}</p>
                    <p>🔄 Reviews: ${clip.review_count || 0}</p>
                    <div style="margin-top:0.5rem;">
                        <a href="/watch/${clip.clip_id}" class="btn btn-primary" style="font-size:0.75rem;padding:0.25rem 0.5rem;">Watch</a>
                        <a href="/lipsync/${clip.clip_id}" class="btn btn-secondary" style="font-size:0.75rem;padding:0.25rem 0.5rem;">Lip Sync</a>
                    </div>
                `;
                clipsList.appendChild(card);
            });
        } catch (err) {
            clipsList.innerHTML = `<p class="loading">Error loading clips: ${err.message}</p>`;
        }
    }

    exportBtn.addEventListener('click', async () => {
        try {
            const res = await fetch('/api/export', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ deck_name: 'Video Babbel' }),
            });
            const data = await res.json();
            if (data.status) {
                alert('Export complete! Check your downloads folder.');
            } else {
                alert('Export failed: ' + data.error);
            }
        } catch (err) {
            alert('Export error: ' + err.message);
        }
    });
});
