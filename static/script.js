document.addEventListener('DOMContentLoaded', () => {
    let ruinChartInstance = null;
    let assetChartInstance = null;

    document.getElementById('simForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const runBtn = document.getElementById('runBtn');
        runBtn.textContent = '模拟中...';
        runBtn.disabled = true;

        const data = {
            current_age: document.getElementById('current_age').value,
            life_expectancy: document.getElementById('life_expectancy').value,
            current_assets: document.getElementById('current_assets').value,
            annual_income: document.getElementById('annual_income').value,
            annual_expense: document.getElementById('annual_expense').value,
            post_retirement_income: document.getElementById('post_retirement_income').value,
            simulations: document.getElementById('simulations').value
        };

        try {
            const response = await fetch('/api/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const results = await response.json();
            updateCharts(results);

        } catch (error) {
            console.error(error);
            alert('模拟失败，请检查控制台。');
        } finally {
            runBtn.textContent = '开始模拟';
            runBtn.disabled = false;
        }
    });

    function updateCharts(results) {
        // --- 1. Ruin Probability Chart ---
        const ruinLabels = results.ruin_rates.map(r => r.age);
        const ruinData = results.ruin_rates.map(r => r.rate);
        const ctxRuin = document.getElementById('ruinChart').getContext('2d');

        if (ruinChartInstance) ruinChartInstance.destroy();

        ruinChartInstance = new Chart(ctxRuin, {
            type: 'line',
            data: {
                labels: ruinLabels,
                datasets: [{
                    label: '破产概率 (%)',
                    data: ruinData,
                    borderColor: '#ff4d4d',
                    backgroundColor: 'rgba(255, 77, 77, 0.2)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, grid: { color: '#444' } },
                    x: { grid: { color: '#444' } }
                },
                plugins: {
                    legend: { labels: { color: 'white' } },
                    annotation: {
                        annotations: {
                            line1: {
                                type: 'line', yMin: 5, yMax: 5,
                                borderColor: 'rgb(0, 255, 0)', borderWidth: 2, borderDash: [5, 5],
                                label: { content: '5% 安全线', enabled: true, color: 'white' }
                            }
                        }
                    }
                }
            }
        });

        // --- 2. Helper to render Asset Charts ---
        const renderAssetChart = (canvasId, data, title) => {
            const ctx = document.getElementById(canvasId).getContext('2d');
            // Clean up existing instance if attached to the element
            const existingChart = Chart.getChart(canvasId);
            if (existingChart) existingChart.destroy();

            if (!data) {
                // Handle case where age is below current age
                ctx.font = '16px Inter';
                ctx.fillStyle = '#888';
                ctx.textAlign = 'center';
                ctx.fillText('此年龄段不可用', ctx.canvas.width / 2, ctx.canvas.height / 2);
                return null;
            }

            return new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.ages,
                    datasets: [
                        { label: 'P90 (乐观)', data: data.p90, borderColor: '#03dac6', borderDash: [5, 5], fill: false },
                        { label: 'P50 (中性)', data: data.p50, borderColor: '#bb86fc', fill: false },
                        { label: 'P10 (悲观)', data: data.p10, borderColor: '#cf6679', borderDash: [5, 5], fill: false }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    scales: {
                        y: { grid: { color: '#444' }, title: { display: true, text: '资产 (万元)', color: 'white' } },
                        x: { grid: { color: '#444' } }
                    },
                    plugins: {
                        legend: { position: 'top', labels: { color: 'white', boxWidth: 10, font: { size: 10 } } },
                        title: { display: true, text: title, color: 'white' }
                    }
                }
            });
        };

        // Render the 3 Asset Charts
        renderAssetChart('assetChart', results.projections.recommended, `推荐退休年龄: ${results.projections.recommended.retire_age} 岁`);
        renderAssetChart('assetChart30', results.projections.age_30, `30 岁退休走势`);
        renderAssetChart('assetChart40', results.projections.age_40, `40 岁退休走势`);
    }
});
