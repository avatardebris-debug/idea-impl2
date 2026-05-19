// lipsync.js — Lip sync page logic

document.addEventListener('DOMContentLoaded', () => {
    const clipId = window.location.pathname.split('/lipsync/')[1];
    const statusEl = document.getElementById('lipsync-status');
    const resultEl = document.getElementById('lipsync-result');
    const originalVideo = document.getElementById('original-video');
    const lipsyncVideo = document.getElementById('lipsync-video');

    // Load original video
    originalVideo.querySelector('source').src = `/clips/${clipId}.mp4`;
    originalVideo.load();

    // Generate lip sync
    async function generateLipSync() {
        statusEl.style.display = 'block';
        resultEl.style.display = 'none';

        try {
            const res = await fetch(`/api/lipsync/${clipId}`, {
                method: 'POST',
            });
            const data = await res.json();
            if (data.status) {
                statusEl.style.display = 'none';
                resultEl.style.display = 'block';
                lipsyncVideo.querySelector('source').src = `/clips/${clipId}_lipsync.mp4`;
                lipsyncVideo.load();
            } else {
                statusEl.innerHTML = `<p style="color:var(--danger);">Error: ${data.error}</p>`;
            }
        } catch (err) {
            statusEl.innerHTML = `<p style="color:var(--danger);">Error: ${err.message}</p>`;
        }
    }

    generateLipSync();
});
