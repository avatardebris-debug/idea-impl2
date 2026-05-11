/**
 * Dashboard JavaScript - loads data from API and renders charts.
 */

function loadDashboardData() {
    fetch('/api/dashboard/summary')
        .then(res => res.json())
        .then(data => {
            // Update stats
            document.getElementById('total-filings').textContent = data.total_filings || 0;
            document.getElementById('total-companies').textContent = data.total_companies || 0;
            document.getElementById('total-fraud-scores').textContent = data.total_fraud_scores || 0;
            document.getElementById('total-red-flags').textContent = data.total_red_flags || 0;
            document.getElementById('total-capital-flows').textContent = data.total_capital_flows || 0;

            // Risk distribution chart
            const riskLabels = Object.keys(data.risk_distribution || {});
            const riskValues = Object.values(data.risk_distribution || {});
            const riskColors = riskLabels.map(l => {
                if (l === 'high') return '#e74c3c';
                if (l === 'medium') return '#f39c12';
                return '#2ecc71';
            });
            new Chart(document.getElementById('risk-chart'), {
                type: 'doughnut',
                data: {
                    labels: riskLabels,
                    datasets: [{ data: riskValues, backgroundColor: riskColors }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });

            // Category distribution chart
            const catLabels = Object.keys(data.category_distribution || {});
            const catValues = Object.values(data.category_distribution || {});
            new Chart(document.getElementById('category-chart'), {
                type: 'bar',
                data: {
                    labels: catLabels,
                    datasets: [{ label: 'Count', data: catValues, backgroundColor: '#3498db' }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });

            // Recent scores table
            const scoresBody = document.querySelector('#recent-scores-table tbody');
            (data.recent_scores || []).forEach(s => {
                const row = document.createElement('tr');
                row.innerHTML = `<td>${s.ticker}</td><td>${s.fraud_score}</td><td>${s.risk_level}</td><td>${s.filing_date}</td>`;
                scoresBody.appendChild(row);
            });

            // Top flags table
            const flagsBody = document.querySelector('#top-flags-table tbody');
            (data.top_flags || []).forEach(f => {
                const row = document.createElement('tr');
                row.innerHTML = `<td>${f.category}</td><td>${f.cnt}</td>`;
                flagsBody.appendChild(row);
            });
        })
        .catch(err => console.error('Error loading dashboard:', err));
}

function loadTickerData(ticker) {
    // Load company info
    fetch(`/api/companies?ticker=${ticker}`)
        .then(res => res.json())
        .then(data => {
            const infoDiv = document.getElementById('company-info');
            if (data.companies && data.companies.length > 0) {
                const c = data.companies[0];
                infoDiv.innerHTML = `
                    <p><strong>Name:</strong> ${c.name || '-'}</p>
                    <p><strong>CIK:</strong> ${c.cik || '-'}</p>
                    <p><strong>SIC:</strong> ${c.sic || '-'}</p>
                    <p><strong>Industry:</strong> ${c.industry || '-'}</p>
                    <p><strong>State:</strong> ${c.state || '-'}</p>
                `;
            } else {
                infoDiv.innerHTML = '<p>No company data found.</p>';
            }
        })
        .catch(err => console.error('Error loading company info:', err));

    // Load fraud scores
    fetch(`/api/fraud-scores?ticker=${ticker}`)
        .then(res => res.json())
        .then(data => {
            const summaryDiv = document.getElementById('fraud-summary');
            const scores = data.scores || [];
            if (scores.length > 0) {
                const latest = scores[0];
                summaryDiv.innerHTML = `
                    <p><strong>Latest Score:</strong> ${latest.fraud_score}</p>
                    <p><strong>Risk Level:</strong> ${latest.risk_level}</p>
                    <p><strong>Filing Date:</strong> ${latest.filing_date}</p>
                    <p><strong>Total Scores:</strong> ${scores.length}</p>
                `;

                // Fraud trend chart
                const ctx = document.getElementById('fraud-trend-chart');
                if (ctx) {
                    new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: scores.map(s => s.filing_date),
                            datasets: [{
                                label: 'Fraud Score',
                                data: scores.map(s => s.fraud_score),
                                borderColor: '#e74c3c',
                                tension: 0.1
                            }]
                        },
                        options: { responsive: true, maintainAspectRatio: false }
                    });
                }
            } else {
                summaryDiv.innerHTML = '<p>No fraud scores found.</p>';
            }
        })
        .catch(err => console.error('Error loading fraud scores:', err));

    // Load red flags
    fetch(`/api/red-flags?ticker=${ticker}`)
        .then(res => res.json())
        .then(data => {
            const summaryDiv = document.getElementById('red-flag-summary');
            const flags = data.flags || [];
            if (flags.length > 0) {
                const highCount = flags.filter(f => f.severity === 'high').length;
                const medCount = flags.filter(f => f.severity === 'medium').length;
                const lowCount = flags.filter(f => f.severity === 'low').length;
                summaryDiv.innerHTML = `
                    <p><strong>Total Flags:</strong> ${flags.length}</p>
                    <p><strong>High Severity:</strong> ${highCount}</p>
                    <p><strong>Medium Severity:</strong> ${medCount}</p>
                    <p><strong>Low Severity:</strong> ${lowCount}</p>
                `;

                // Red flags by category chart
                const catCounts = {};
                flags.forEach(f => { catCounts[f.category] = (catCounts[f.category] || 0) + 1; });
                const ctx = document.getElementById('red-flags-chart');
                if (ctx) {
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: Object.keys(catCounts),
                            datasets: [{ label: 'Count', data: Object.values(catCounts), backgroundColor: '#f39c12' }]
                        },
                        options: { responsive: true, maintainAspectRatio: false }
                    });
                }

                // Recent flags table
                const flagsBody = document.querySelector('#recent-flags-table tbody');
                (flags.slice(0, 10)).forEach(f => {
                    const row = document.createElement('tr');
                    row.innerHTML = `<td>${f.filing_date}</td><td>${f.category}</td><td>${f.severity}</td><td>${f.description}</td>`;
                    flagsBody.appendChild(row);
                });
            } else {
                summaryDiv.innerHTML = '<p>No red flags found.</p>';
            }
        })
        .catch(err => console.error('Error loading red flags:', err));

    // Load capital flows
    fetch(`/api/capital-flows?ticker=${ticker}`)
        .then(res => res.json())
        .then(data => {
            const summaryDiv = document.getElementById('capital-flow-summary');
            const flows = data.flows || [];
            if (flows.length > 0) {
                const latest = flows[0];
                summaryDiv.innerHTML = `
                    <p><strong>Latest Period:</strong> ${latest.period_label}</p>
                    <p><strong>Operating Cash Flow:</strong> ${latest.operating_cash_flow}</p>
                    <p><strong>Free Cash Flow:</strong> ${latest.free_cash_flow}</p>
                    <p><strong>Total Flows:</strong> ${flows.length}</p>
                `;

                // Capital flows chart
                const ctx = document.getElementById('capital-flows-chart');
                if (ctx) {
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: flows.map(f => f.period_label),
                            datasets: [
                                { label: 'Operating', data: flows.map(f => f.operating_cash_flow), backgroundColor: '#2ecc71' },
                                { label: 'Investing', data: flows.map(f => f.investing_cash_flow), backgroundColor: '#3498db' },
                                { label: 'Financing', data: flows.map(f => f.financing_cash_flow), backgroundColor: '#9b59b6' }
                            ]
                        },
                        options: { responsive: true, maintainAspectRatio: false }
                    });
                }
            } else {
                summaryDiv.innerHTML = '<p>No capital flows found.</p>';
            }
        })
        .catch(err => console.error('Error loading capital flows:', err));
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    const ticker = window.ticker;
    if (ticker) {
        loadTickerData(ticker);
    } else {
        loadDashboardData();
    }
});
