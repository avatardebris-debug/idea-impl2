// upload.js — Upload page logic

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('upload-form');
    const status = document.getElementById('status');
    const result = document.getElementById('result');
    const resultText = document.getElementById('result-text');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        status.style.display = 'block';
        status.className = 'status';
        status.textContent = 'Uploading video...';
        result.style.display = 'none';

        const formData = new FormData();
        const videoFile = document.getElementById('video').files[0];
        formData.append('video', videoFile);

        try {
            // Step 1: Upload
            const uploadRes = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            });
            const uploadData = await uploadRes.json();
            if (!uploadData.status) {
                throw new Error(uploadData.error || 'Upload failed');
            }

            status.textContent = 'Extracting clips... This may take a while.';

            // Step 2: Extract
            const extractRes = await fetch('/api/extract', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    video_path: uploadData.video_path,
                    target_lang: document.getElementById('target_lang').value,
                    source_lang: document.getElementById('source_lang').value,
                    top_n: parseInt(document.getElementById('top_n').value),
                }),
            });
            const extractData = await extractRes.json();
            if (!extractData.status) {
                throw new Error(extractData.error || 'Extraction failed');
            }

            status.style.display = 'none';
            result.style.display = 'block';
            resultText.textContent = `${extractData.clips_extracted} clips extracted and ${extractData.clips_imported} imported to database.`;
        } catch (err) {
            status.className = 'status';
            status.style.background = '#fef2f2';
            status.style.borderColor = '#fecaca';
            status.textContent = `Error: ${err.message}`;
        }
    });
});
