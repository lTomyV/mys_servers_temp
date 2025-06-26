// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get elements
    const simulateBtn = document.getElementById('simulate-btn');
    const statusMessage = document.getElementById('status-message');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const dashboard = document.getElementById('dashboard');
    const welcomeMessage = document.getElementById('welcome-message');
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modal-title');
    const modalExplanation = document.getElementById('modal-explanation');
    const closeButton = document.querySelector('.close-button');
    
    // Chart.js default configuration
    Chart.defaults.color = '#2c3e50';
    Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
    
    // Store chart instances for later reference
    let charts = {};
    
    // Get explanations from the server
    let explanations = {};
    
    // Close the modal when clicking the close button
    closeButton.addEventListener('click', function() {
        modal.style.display = 'none';
    });
    
    // Close the modal when clicking outside of it
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Close the modal with Escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && modal.style.display === 'block') {
            modal.style.display = 'none';
        }
    });
    
    // Handle simulation button click
    simulateBtn.addEventListener('click', function() {
        // Disable button during simulation
        simulateBtn.disabled = true;
        simulateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Simulando...';
        
        // Show progress
        statusMessage.textContent = 'Iniciando simulación...';
        progressContainer.classList.remove('hidden');
        
        // Animate progress bar
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 1;
            progressBar.style.width = `${progress}%`;
            
            // Update status message based on progress
            if (progress === 20) {
                statusMessage.textContent = 'Generando perfiles climáticos...';
            } else if (progress === 40) {
                statusMessage.textContent = 'Simulando estrategia de línea base...';
            } else if (progress === 60) {
                statusMessage.textContent = 'Simulando estrategia optimizada...';
            } else if (progress === 80) {
                statusMessage.textContent = 'Analizando resultados...';
            } else if (progress >= 100) {
                clearInterval(progressInterval);
                statusMessage.textContent = 'Procesando gráficos...';
            }
        }, 50);
        
        // Show animation during simulation
        showSimulationAnimation();
        
        // Call the API to simulate
        fetch('/api/simulate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            // Clear any existing charts
            dashboard.innerHTML = '';
            
            // Create charts
            createTemperatureHeatmap(data.hourly_temps);
            createCostHistogram(data.costs_baseline, data.baseline_stats, 'Línea Base', 'cost_baseline');
            createCostHistogram(data.costs_optimized, data.optimized_stats, 'Optimizada', 'cost_optimized');
            createComparisonChart(data.baseline_stats, data.optimized_stats, data.improvement);
            
            // Update status
            clearInterval(progressInterval);
            progressBar.style.width = '100%';
            statusMessage.textContent = 'Simulación completada';
            simulateBtn.disabled = false;
            simulateBtn.innerHTML = '<i class="fas fa-play-circle"></i> Nueva Simulación';
        })
        .catch(error => {
            console.error('Error en la simulación:', error);
            statusMessage.textContent = 'Error en la simulación';
            simulateBtn.disabled = false;
            simulateBtn.innerHTML = '<i class="fas fa-play-circle"></i> Reintentar Simulación';
        });
    });
    
    // Show simulation animation
    function showSimulationAnimation() {
        // Clear dashboard
        dashboard.innerHTML = '';
        
        // Create animation container
        const animTemplate = document.getElementById('animation-template');
        const animClone = document.importNode(animTemplate.content, true);
        dashboard.appendChild(animClone);
        
        // Update temperature display with random values
        const tempDisplay = dashboard.querySelector('.temp-value');
        const tempInterval = setInterval(() => {
            const randomTemp = (22 + Math.random() * 6).toFixed(1);
            tempDisplay.textContent = `${randomTemp}°C`;
        }, 2000);
        
        // Clear animation after simulation completes
        setTimeout(() => {
            clearInterval(tempInterval);
        }, 10000);
    }
    
    // Create temperature heatmap
    function createTemperatureHeatmap(hourlyTemps) {
        // Create card from template
        const cardTemplate = document.getElementById('heatmap-template');
        const cardClone = document.importNode(cardTemplate.content, true);
        
        // Set title and explanation
        cardClone.querySelector('.chart-title').textContent = 'Distribución de Temperaturas Horarias';
        cardClone.querySelector('.chart-explanation').textContent = explanations.temperature_distribution || 
            'Este gráfico muestra la distribución de temperaturas horarias durante el mes de enero.';
        
        // Get container for the heatmap
        const container = cardClone.querySelector('.heatmap-container');
        container.id = 'temperature-heatmap';
        
        // Add to dashboard
        dashboard.appendChild(cardClone);
        
        // Process data for heatmap
        const heatmapData = {
            max: Math.max(...hourlyTemps.map(item => item.temperature)),
            min: Math.min(...hourlyTemps.map(item => item.temperature)),
            data: hourlyTemps.map(item => ({
                x: item.hour * 20 + 10, // Scale to fit container
                y: item.day * 20 - 10,  // Scale to fit container
                value: item.temperature
            }))
        };
        
        // Create heatmap
        const heatmapInstance = h337.create({
            container: document.getElementById('temperature-heatmap'),
            radius: 15,
            maxOpacity: 0.8,
            minOpacity: 0.3,
            blur: 0.8,
            gradient: {
                0.2: 'blue',
                0.4: 'cyan',
                0.6: 'lime',
                0.8: 'yellow',
                1.0: 'red'
            }
        });
        
        heatmapInstance.setData(heatmapData);
        
        // Add hour labels
        const hourLabels = document.createElement('div');
        hourLabels.className = 'hour-labels';
        hourLabels.style.position = 'absolute';
        hourLabels.style.bottom = '5px';
        hourLabels.style.left = '0';
        hourLabels.style.width = '100%';
        hourLabels.style.display = 'flex';
        hourLabels.style.justifyContent = 'space-between';
        hourLabels.style.padding = '0 10px';
        hourLabels.style.fontSize = '12px';
        
        for (let i = 0; i < 24; i += 4) {
            const label = document.createElement('span');
            label.textContent = `${i}:00`;
            hourLabels.appendChild(label);
        }
        
        document.getElementById('temperature-heatmap').appendChild(hourLabels);
        
        // Add day labels
        const dayLabels = document.createElement('div');
        dayLabels.className = 'day-labels';
        dayLabels.style.position = 'absolute';
        dayLabels.style.top = '50%';
        dayLabels.style.left = '5px';
        dayLabels.style.transform = 'translateY(-50%)';
        dayLabels.style.display = 'flex';
        dayLabels.style.flexDirection = 'column';
        dayLabels.style.justifyContent = 'space-between';
        dayLabels.style.height = '80%';
        dayLabels.style.fontSize = '12px';
        
        for (let i = 1; i <= 31; i += 5) {
            const label = document.createElement('span');
            label.textContent = `Día ${i}`;
            dayLabels.appendChild(label);
        }
        
        document.getElementById('temperature-heatmap').appendChild(dayLabels);
        
        // Add expand button functionality
        const expandBtn = container.closest('.graph-card').querySelector('.btn-expand');
        expandBtn.addEventListener('click', function() {
            expandHeatmap('Distribución de Temperaturas Horarias', heatmapData, explanations.temperature_distribution);
        });
    }
    
    // Create cost histogram
    function createCostHistogram(costs, stats, strategy, chartId) {
        // Create card from template
        const cardTemplate = document.getElementById('chart-template');
        const cardClone = document.importNode(cardTemplate.content, true);
        
        // Set title and explanation
        cardClone.querySelector('.chart-title').textContent = `Distribución de Costos - ${strategy}`;
        cardClone.querySelector('.chart-explanation').textContent = explanations[chartId] || 
            `Este histograma muestra la distribución de probabilidad del costo mensual de energía utilizando la estrategia ${strategy.toLowerCase()}.`;
        
        // Get canvas for the chart
        const canvas = cardClone.querySelector('.chart-canvas');
        canvas.id = chartId;
        
        // Add to dashboard
        dashboard.appendChild(cardClone);
        
        // Calculate histogram bins
        const min = Math.min(...costs);
        const max = Math.max(...costs);
        const binWidth = (max - min) / 20;
        const bins = Array(20).fill(0);
        
        costs.forEach(cost => {
            const binIndex = Math.min(Math.floor((cost - min) / binWidth), 19);
            bins[binIndex]++;
        });
        
        const binLabels = Array(20).fill(0).map((_, i) => (min + (i + 0.5) * binWidth).toFixed(2));
        
        // Create chart
        const ctx = document.getElementById(chartId).getContext('2d');
        const chartColor = strategy === 'Línea Base' ? 'rgba(52, 152, 219, 0.7)' : 'rgba(46, 204, 113, 0.7)';
        const chartBorderColor = strategy === 'Línea Base' ? 'rgb(41, 128, 185)' : 'rgb(39, 174, 96)';
        
        charts[chartId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: binLabels,
                datasets: [{
                    label: `Costo Mensual (${strategy})`,
                    data: bins,
                    backgroundColor: chartColor,
                    borderColor: chartBorderColor,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    annotation: {
                        annotations: {
                            meanLine: {
                                type: 'line',
                                yMin: 0,
                                yMax: Math.max(...bins),
                                xMin: stats.mean,
                                xMax: stats.mean,
                                borderColor: 'rgb(231, 76, 60)',
                                borderWidth: 2,
                                borderDash: [5, 5],
                                label: {
                                    content: `Media: $${stats.mean}`,
                                    enabled: true,
                                    position: 'top'
                                }
                            },
                            costo90Line: {
                                type: 'line',
                                yMin: 0,
                                yMax: Math.max(...bins),
                                xMin: stats.costo90,
                                xMax: stats.costo90,
                                borderColor: 'rgb(142, 68, 173)',
                                borderWidth: 2,
                                borderDash: [5, 5],
                                label: {
                                    content: `Costo90: $${stats.costo90}`,
                                    enabled: true,
                                    position: 'top'
                                }
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            title: function(tooltipItems) {
                                const item = tooltipItems[0];
                                const binStart = (min + item.dataIndex * binWidth).toFixed(2);
                                const binEnd = (min + (item.dataIndex + 1) * binWidth).toFixed(2);
                                return `Rango: $${binStart} - $${binEnd}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Costo Mensual (U$D)'
                        },
                        ticks: {
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Frecuencia'
                        },
                        beginAtZero: true
                    }
                }
            }
        });
        
        // Add expand button functionality
        const expandBtn = canvas.closest('.graph-card').querySelector('.btn-expand');
        expandBtn.addEventListener('click', function() {
            expandChart(chartId, `Distribución de Costos - ${strategy}`, explanations[chartId]);
        });
    }
    
    // Create comparison chart
    function createComparisonChart(baselineStats, optimizedStats, improvement) {
        // Create card from template
        const cardTemplate = document.getElementById('chart-template');
        const cardClone = document.importNode(cardTemplate.content, true);
        
        // Set title and explanation
        cardClone.querySelector('.chart-title').textContent = 'Comparación de Estrategias';
        cardClone.querySelector('.chart-explanation').textContent = explanations.randomization || 
            'Este gráfico compara el rendimiento de las estrategias de control, mostrando la reducción en costos y riesgo financiero lograda con la estrategia optimizada.';
        
        // Get canvas for the chart
        const canvas = cardClone.querySelector('.chart-canvas');
        canvas.id = 'comparison-chart';
        
        // Add to dashboard
        dashboard.appendChild(cardClone);
        
        // Create chart
        const ctx = document.getElementById('comparison-chart').getContext('2d');
        
        charts['comparison'] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Costo Promedio', 'Costo90 (Riesgo)'],
                datasets: [
                    {
                        label: 'Línea Base',
                        data: [baselineStats.mean, baselineStats.costo90],
                        backgroundColor: 'rgba(52, 152, 219, 0.7)',
                        borderColor: 'rgb(41, 128, 185)',
                        borderWidth: 1
                    },
                    {
                        label: 'Optimizada',
                        data: [optimizedStats.mean, optimizedStats.costo90],
                        backgroundColor: 'rgba(46, 204, 113, 0.7)',
                        borderColor: 'rgb(39, 174, 96)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            afterLabel: function(context) {
                                const dataIndex = context.dataIndex;
                                const label = context.chart.data.labels[dataIndex];
                                const improvementValue = label === 'Costo Promedio' ? improvement.mean : improvement.costo90;
                                return `Mejora: ${improvementValue}%`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Métrica'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Costo (U$D)'
                        },
                        beginAtZero: true
                    }
                }
            }
        });
        
        // Add expand button functionality
        const expandBtn = canvas.closest('.graph-card').querySelector('.btn-expand');
        expandBtn.addEventListener('click', function() {
            expandChart('comparison', 'Comparación de Estrategias', explanations.randomization);
        });
    }
    
    // Function to expand a chart in the modal
    function expandChart(chartId, title, explanation) {
        const modal = document.getElementById('modal');
        const modalTitle = document.getElementById('modal-title');
        const modalExplanation = document.getElementById('modal-explanation');
        const modalChartContainer = document.getElementById('modal-chart-container');
        
        // Set modal content
        modalTitle.textContent = title;
        modalExplanation.textContent = explanation || '';
        
        // Create a new canvas for the modal chart
        modalChartContainer.innerHTML = '';
        const canvas = document.createElement('canvas');
        canvas.id = 'modal-chart';
        modalChartContainer.appendChild(canvas);
        
        // Show the modal
        modal.style.display = 'block';
        
        // Clone the chart configuration
        const originalChart = charts[chartId];
        const ctx = document.getElementById('modal-chart').getContext('2d');
        
        // Create a new chart with the same configuration
        new Chart(ctx, {
            type: originalChart.config.type,
            data: JSON.parse(JSON.stringify(originalChart.config.data)),
            options: JSON.parse(JSON.stringify(originalChart.config.options))
        });
    }
    
    // Function to expand a heatmap in the modal
    function expandHeatmap(title, data, explanation) {
        const modal = document.getElementById('modal');
        const modalTitle = document.getElementById('modal-title');
        const modalExplanation = document.getElementById('modal-explanation');
        const modalChartContainer = document.getElementById('modal-chart-container');
        
        // Set modal content
        modalTitle.textContent = title;
        modalExplanation.textContent = explanation || '';
        
        // Create a new div for the modal heatmap
        modalChartContainer.innerHTML = '';
        const heatmapDiv = document.createElement('div');
        heatmapDiv.id = 'modal-heatmap';
        heatmapDiv.style.width = '100%';
        heatmapDiv.style.height = '100%';
        modalChartContainer.appendChild(heatmapDiv);
        
        // Show the modal
        modal.style.display = 'block';
        
        // Create heatmap
        const heatmapInstance = h337.create({
            container: document.getElementById('modal-heatmap'),
            radius: 20,
            maxOpacity: 0.8,
            minOpacity: 0.3,
            blur: 0.8,
            gradient: {
                0.2: 'blue',
                0.4: 'cyan',
                0.6: 'lime',
                0.8: 'yellow',
                1.0: 'red'
            }
        });
        
        heatmapInstance.setData(data);
        
        // Add hour labels
        const hourLabels = document.createElement('div');
        hourLabels.className = 'hour-labels';
        hourLabels.style.position = 'absolute';
        hourLabels.style.bottom = '5px';
        hourLabels.style.left = '0';
        hourLabels.style.width = '100%';
        hourLabels.style.display = 'flex';
        hourLabels.style.justifyContent = 'space-between';
        hourLabels.style.padding = '0 20px';
        
        for (let i = 0; i < 24; i += 2) {
            const label = document.createElement('span');
            label.textContent = `${i}:00`;
            hourLabels.appendChild(label);
        }
        
        document.getElementById('modal-heatmap').appendChild(hourLabels);
        
        // Add day labels
        const dayLabels = document.createElement('div');
        dayLabels.className = 'day-labels';
        dayLabels.style.position = 'absolute';
        dayLabels.style.top = '50%';
        dayLabels.style.left = '10px';
        dayLabels.style.transform = 'translateY(-50%)';
        dayLabels.style.display = 'flex';
        dayLabels.style.flexDirection = 'column';
        dayLabels.style.justifyContent = 'space-between';
        dayLabels.style.height = '80%';
        
        for (let i = 1; i <= 31; i += 3) {
            const label = document.createElement('span');
            label.textContent = `Día ${i}`;
            dayLabels.appendChild(label);
        }
        
        document.getElementById('modal-heatmap').appendChild(dayLabels);
    }
    
    // Get explanations from the server
    function fetchExplanations() {
        const explanationElements = document.querySelectorAll('[data-explanation]');
        explanationElements.forEach(el => {
            const key = el.getAttribute('data-explanation');
            explanations[key] = el.textContent;
        });
    }
    
    // Initialize
    fetchExplanations();
}); 