// Forensic Suite - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Auto-refresh dashboard every 5 minutes
    if (window.location.pathname === '/') {
        setInterval(() => {
            window.location.reload();
        }, 300000);
    }

    // Search functionality
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function() {
            const query = this.value.toLowerCase();
            const rows = document.querySelectorAll('.data-table tbody tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query) ? '' : 'none';
            });
        }, 300));
    }
});

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
