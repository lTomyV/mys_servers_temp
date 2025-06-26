// Variables globales
let simulationRunning = false;
let statusCheckInterval = null;
let chartInstances = {};

// Configuración por defecto para los gráficos
const defaultChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
        mode: 'index',
        intersect: false,
    },
    plugins: {
        legend: {
            position: 'top',
            labels: {
                boxWidth: 15,
                font: {
                    size: 11
                }
            }
        },
        tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
                label: function(context) {
                    let label = context.dataset.label || '';
                    if (label) {
                        label += ': ';
                    }
                    if (context.parsed.y !== null) {
                        label += context.parsed.y.toFixed(2);
                    }
                    return label;
                }
            }
        }
    },
    scales: {
        x: {
            grid: {
                display: false
            },
            ticks: {
                maxRotation: 90,
                minRotation: 45,
                font: {
                    size: 10
                }
            }
        },
        y: {
            grid: {
                color: '#e0e0e0'
            }
        }
    }
};

// Función para inicializar la página
document.addEventListener('DOMContentLoaded', function() {
    console.log("Documento cargado, inicializando...");
    
    // Configurar botón de simulación
    const simulateButton = document.getElementById('simulate-button');
    if (simulateButton) {
        simulateButton.addEventListener('click', startSimulation);
        console.log("Botón de simulación configurado");
    } else {
        console.error("No se encontró el botón de simulación");
    }
    
    // Inicializar selectores de modelo de refrigeración
    initModeloRefrigeracionSelector();
    
    // Mostrar explicaciones al hacer hover
    setupExplanationHovers();
    
    // Modal
    initModal();
});

// Inicializar selector de modelo de refrigeración
function initModeloRefrigeracionSelector() {
    const modeloSelector = document.getElementById('modelo-refrigeracion');
    
    if (modeloSelector) {
        console.log("Inicializando selector de modelos...");
        
        // Ya tenemos opciones predeterminadas en el HTML, así que solo intentamos actualizar con datos del servidor
        fetch('/api/modelos_refrigeracion')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error de red: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log("Datos de modelos recibidos:", data);
                
                if (Object.keys(data).length > 0) {
                    // Limpiar opciones existentes
                    modeloSelector.innerHTML = '';
                    
                    // Añadir nuevas opciones
                    Object.keys(data).forEach(key => {
                        const option = document.createElement('option');
                        option.value = key;
                        option.textContent = data[key].nombre;
                        
                        // Seleccionar el modelo eficiente por defecto
                        if (key === 'eficiente') {
                            option.selected = true;
                        }
                        
                        modeloSelector.appendChild(option);
                    });
                    
                    console.log("Selector de modelos configurado con", Object.keys(data).length, "opciones");
                } else {
                    console.warn("No se recibieron datos de modelos válidos");
                }
            })
            .catch(error => {
                console.error('Error al cargar modelos de refrigeración:', error);
                console.log("Usando opciones predeterminadas del HTML");
            });
    } else {
        console.error("No se encontró el elemento 'modelo-refrigeracion'");
    }
}

// Función para iniciar la simulación
function startSimulation() {
    if (simulationRunning) {
        console.log("Simulación ya en curso, ignorando solicitud");
        return;
    }
    
    // Obtener modelo de refrigeración seleccionado
    const modeloSelector = document.getElementById('modelo-refrigeracion');
    const modeloSeleccionado = modeloSelector ? modeloSelector.value : 'eficiente';
    
    console.log("Iniciando simulación con modelo:", modeloSeleccionado);
    
    // Mostrar spinner y mensaje de simulación
    simulationRunning = true;
    updateUIForSimulationStart();
    
    // Realizar solicitud para iniciar simulación
    fetch('/api/simulate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            modelo: modeloSeleccionado
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Respuesta de inicio de simulación:", data);
        
        if (data.status === 'started') {
            // Iniciar verificación periódica del estado
            statusCheckInterval = setInterval(checkSimulationStatus, 1000);
        } else {
            showError('Error al iniciar la simulación');
            simulationRunning = false;
            updateUIForSimulationEnd();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Error de conexión');
        simulationRunning = false;
        updateUIForSimulationEnd();
    });
}

// Verificar estado de la simulación
function checkSimulationStatus() {
    fetch('/api/simulation_status')
        .then(response => response.json())
        .then(data => {
            console.log("Estado de simulación:", data.status);
            
            if (data.status === 'complete') {
                // Simulación completada
                clearInterval(statusCheckInterval);
                simulationRunning = false;
                updateUIForSimulationEnd();
                displayResults(data);
            } else if (data.status === 'running') {
                // Simulación en curso, actualizar animación
                updateSimulationProgress();
            } else if (data.status === 'error') {
                // Error en la simulación
                clearInterval(statusCheckInterval);
                simulationRunning = false;
                updateUIForSimulationEnd();
                showError(data.message || 'Error durante la simulación');
            }
        })
        .catch(error => {
            console.error('Error al verificar estado:', error);
        });
}

// Actualizar UI cuando inicia la simulación
function updateUIForSimulationStart() {
    const simulateButton = document.getElementById('simulate-button');
    const simulationStatus = document.getElementById('simulation-status');
    const resultsSection = document.getElementById('results-section');
    
    if (simulateButton) {
        simulateButton.disabled = true;
        simulateButton.classList.add('disabled');
        simulateButton.innerHTML = '<span class="spinner"></span> Simulando...';
    }
    
    if (simulationStatus) {
        simulationStatus.textContent = 'Simulando...';
        simulationStatus.style.display = 'block';
        simulationStatus.className = 'status-message status-running';
    }
    
    // Ocultar resultados anteriores
    if (resultsSection) {
        resultsSection.style.opacity = '0.5';
    }
    
    // Mostrar animación de progreso
    const progressContainer = document.getElementById('simulation-progress');
    if (progressContainer) {
        progressContainer.style.display = 'block';
        progressContainer.innerHTML = `
            <div class="progress-animation">
                <div class="progress-step active">Inicializando simulación</div>
                <div class="progress-step">Generando perfiles climáticos</div>
                <div class="progress-step">Calculando dinámica térmica</div>
                <div class="progress-step">Procesando resultados</div>
                <div class="progress-step">Generando visualizaciones</div>
            </div>
        `;
    }
}

// Actualizar progreso de simulación con animación
let currentProgressStep = 0;
function updateSimulationProgress() {
    const progressSteps = document.querySelectorAll('.progress-step');
    if (progressSteps.length === 0) return;
    
    // Avanzar al siguiente paso cada pocos segundos
    currentProgressStep = (currentProgressStep + 1) % (progressSteps.length * 2);
    
    // Actualizar clases de los pasos
    progressSteps.forEach((step, index) => {
        if (index === Math.floor(currentProgressStep / 2)) {
            step.classList.add('active');
            step.classList.remove('completed');
        } else if (index < Math.floor(currentProgressStep / 2)) {
            step.classList.add('completed');
            step.classList.remove('active');
        } else {
            step.classList.remove('active', 'completed');
        }
    });
}

// Actualizar UI cuando finaliza la simulación
function updateUIForSimulationEnd() {
    const simulateButton = document.getElementById('simulate-button');
    const simulationStatus = document.getElementById('simulation-status');
    const progressContainer = document.getElementById('simulation-progress');
    const resultsSection = document.getElementById('results-section');
    
    if (simulateButton) {
        simulateButton.disabled = false;
        simulateButton.classList.remove('disabled');
        simulateButton.innerHTML = 'Simular';
    }
    
    if (simulationStatus) {
        simulationStatus.textContent = 'Simulación completada';
        simulationStatus.className = 'status-message status-complete';
    }
    
    if (progressContainer) {
        progressContainer.style.display = 'none';
    }
    
    if (resultsSection) {
        resultsSection.style.opacity = '1';
        resultsSection.style.display = 'block';
    }
}

// Mostrar resultados de la simulación
function displayResults(data) {
    // Mostrar sección de resultados
    const resultsSection = document.getElementById('results-section');
    if (resultsSection) {
        resultsSection.style.display = 'block';
    }
    
    // Actualizar información del modelo de refrigeración
    updateModeloInfo(data.modelo_refrigeracion);
    
    // Actualizar estadísticas
    updateStatistics(data);
    
    // Actualizar gráficos
    updateAllCharts(data);
    
    // Mostrar tiempo de simulación
    const simulationTime = document.getElementById('simulation-time');
    if (simulationTime && data.simulation_time) {
        simulationTime.textContent = `Tiempo de simulación: ${data.simulation_time} segundos`;
    }
    
    // Hacer scroll a los resultados
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Actualizar información del modelo de refrigeración
function updateModeloInfo(modeloData) {
    if (!modeloData) return;
    
    const modeloInfo = document.getElementById('modelo-info');
    if (!modeloInfo) return;
    
    modeloInfo.innerHTML = `
        <h3>Modelo de Refrigeración: ${modeloData.nombre}</h3>
        <div class="modelo-details">
            <div class="modelo-spec">
                <span class="spec-label">COP Nominal:</span>
                <span class="spec-value">${modeloData.cop_nominal}</span>
            </div>
            <div class="modelo-spec">
                <span class="spec-label">Potencia:</span>
                <span class="spec-value">${modeloData.potencia_nominal} W</span>
            </div>
            <div class="modelo-spec">
                <span class="spec-label">Precio:</span>
                <span class="spec-value">$${modeloData.precio}</span>
            </div>
            <div class="modelo-spec">
                <span class="spec-label">Vida útil:</span>
                <span class="spec-value">${modeloData.vida_util} años</span>
            </div>
            <div class="modelo-spec">
                <span class="spec-label">Mantenimiento anual:</span>
                <span class="spec-value">$${modeloData.mantenimiento_anual}/año</span>
            </div>
        </div>
    `;
}

// Actualizar estadísticas
function updateStatistics(data) {
    // Actualizar estadísticas de costo
    if (data.baseline_stats && data.optimized_stats && data.improvement) {
        const costStats = document.getElementById('cost-stats');
        if (costStats) {
            costStats.innerHTML = `
                <h3>Estadísticas de Costo</h3>
                <table class="stats-table">
                    <thead>
                        <tr>
                            <th>Estadística</th>
                            <th>Línea Base</th>
                            <th>Optimizado</th>
                            <th>Mejora</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Costo Promedio</td>
                            <td>$${data.baseline_stats.mean.toFixed(2)}</td>
                            <td>$${data.optimized_stats.mean.toFixed(2)}</td>
                            <td class="improvement">${data.improvement.mean}%</td>
                        </tr>
                        <tr>
                            <td>Costo90</td>
                            <td>$${data.baseline_stats.costo90.toFixed(2)}</td>
                            <td>$${data.optimized_stats.costo90.toFixed(2)}</td>
                            <td class="improvement">${data.improvement.costo90}%</td>
                        </tr>
                        <tr>
                            <td>Desviación Estándar</td>
                            <td>$${data.baseline_stats.std.toFixed(2)}</td>
                            <td>$${data.optimized_stats.std.toFixed(2)}</td>
                            <td>-</td>
                        </tr>
                        <tr>
                            <td>Costo Mínimo</td>
                            <td>$${data.baseline_stats.min.toFixed(2)}</td>
                            <td>$${data.optimized_stats.min.toFixed(2)}</td>
                            <td>-</td>
                        </tr>
                        <tr>
                            <td>Costo Máximo</td>
                            <td>$${data.baseline_stats.max.toFixed(2)}</td>
                            <td>$${data.optimized_stats.max.toFixed(2)}</td>
                            <td>-</td>
                        </tr>
                    </tbody>
                </table>
            `;
        }
    }
}

// Actualizar todos los gráficos
function updateAllCharts(data) {
    if (data.cop_curves_data) renderCopCurves(data.cop_curves_data);
    if (data.randomization_data) renderRandomizationChart(data.randomization_data);
    if (data.hourly_temp_data) renderHourlyTempChart(data.hourly_temp_data);
    if (data.costs_baseline) updateCostHistogram('baseline-histogram', data.costs_baseline, 'Línea Base', data.baseline_stats);
    if (data.costs_optimized) updateCostHistogram('optimized-histogram', data.costs_optimized, 'Optimizado', data.optimized_stats);

    // Añadir listeners a los botones de expandir (se hace aquí para asegurar que los gráficos existen)
    document.querySelectorAll('.expand-chart-btn').forEach(button => {
        button.onclick = () => openChartInModal(button.dataset.chartCanvas);
    });
}

// --- Funciones de renderizado de gráficos ---

function renderCopCurves(data) {
    const canvasId = 'cop-curves-chart';
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error(`No se encontró el elemento canvas con id ${canvasId}`);
        return;
    }
    
    const chartCtx = ctx.getContext('2d');
    if (chartInstances[canvasId]) chartInstances[canvasId].destroy();

    const datasets = Object.keys(data.curves).map(key => ({
        label: data.curves[key].nombre,
        data: data.curves[key].cops,
        borderColor: data.curves[key].color,
        tension: 0.1,
        fill: false,
    }));

    chartInstances[canvasId] = new Chart(chartCtx, {
        type: 'line',
        data: {
            labels: data.temps,
            datasets: datasets
        },
        options: { 
            ...defaultChartOptions,
            plugins: { 
                ...defaultChartOptions.plugins, 
                title: { 
                    display: true, 
                    text: 'Curvas COP vs Temperatura Exterior' 
                } 
            } 
        }
    });
}

function renderRandomizationChart(data) {
    const canvasId = 'randomization-chart';
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error(`No se encontró el elemento canvas con id ${canvasId}`);
        return;
    }
    
    const chartCtx = ctx.getContext('2d');
    if (chartInstances[canvasId]) chartInstances[canvasId].destroy();

    const { t_mins, t_maxs } = data;
    
    // Lógica de binning
    const createBins = (series) => {
        const min = Math.min(...series);
        const max = Math.max(...series);
        const binCount = 10;
        const binWidth = (max - min) / binCount;
        
        const bins = Array(binCount).fill(0);
        const labels = [];
        
        // Crear etiquetas para los bins
        for (let i = 0; i < binCount; i++) {
            const binStart = min + i * binWidth;
            const binEnd = binStart + binWidth;
            labels.push(`${binStart.toFixed(1)}-${binEnd.toFixed(1)}`);
        }
        
        // Contar valores en cada bin
        series.forEach(value => {
            const binIndex = Math.min(Math.floor((value - min) / binWidth), binCount - 1);
            bins[binIndex]++;
        });
        
        return { counts: bins, labels };
    };
    
    const minBins = createBins(t_mins);
    const maxBins = createBins(t_maxs);

    chartInstances[canvasId] = new Chart(chartCtx, {
        type: 'bar',
        data: {
            labels: minBins.labels,
            datasets: [
                { label: 'T Mínima', data: minBins.counts, backgroundColor: 'rgba(54, 162, 235, 0.6)' },
                { label: 'T Máxima', data: maxBins.counts, backgroundColor: 'rgba(255, 99, 132, 0.6)' }
            ]
        },
        options: { 
            ...defaultChartOptions, 
            scales: { 
                x: { 
                    ...defaultChartOptions.scales.x, 
                    stacked: true 
                }, 
                y: { 
                    ...defaultChartOptions.scales.y, 
                    stacked: true 
                } 
            } 
        }
    });
}

function renderHourlyTempChart(data) {
    const canvasId = 'hourly-temp-chart';
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error(`No se encontró el elemento canvas con id ${canvasId}`);
        return;
    }
    
    const chartCtx = ctx.getContext('2d');
    if (chartInstances[canvasId]) chartInstances[canvasId].destroy();

    const hourLabels = Array.from({length: 24}, (_, i) => `${i}:00`);
    
    const options = {
        ...defaultChartOptions,
        plugins: {
            ...defaultChartOptions.plugins
        }
    };
    
    // Añadir anotaciones si el plugin está disponible
    if (Chart.annotation) {
        options.plugins.annotation = {
            annotations: {
                minHour: {
                    type: 'point',
                    xValue: data.min_hour,
                    yValue: data.hourly_means[data.min_hour],
                    backgroundColor: 'rgba(54, 162, 235, 0.8)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 2,
                    radius: 5,
                    label: {
                        content: `Mín: ${data.hourly_means[data.min_hour].toFixed(1)}°C`,
                        enabled: true,
                        position: 'top'
                    }
                },
                maxHour: {
                    type: 'point',
                    xValue: data.max_hour,
                    yValue: data.hourly_means[data.max_hour],
                    backgroundColor: 'rgba(255, 99, 132, 0.8)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 2,
                    radius: 5,
                    label: {
                        content: `Máx: ${data.hourly_means[data.max_hour].toFixed(1)}°C`,
                        enabled: true,
                        position: 'top'
                    }
                }
            }
        };
    }
    
    chartInstances[canvasId] = new Chart(chartCtx, {
        type: 'line',
        data: {
            labels: hourLabels,
            datasets: [{
                label: 'Temperatura Media (°C)',
                data: data.hourly_means,
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                fill: true,
                tension: 0.4
            }]
        },
        options: options
    });
}

function updateCostHistogram(canvasId, costs, label, stats) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) {
        console.error(`No se encontró el elemento canvas con id ${canvasId}`);
        return;
    }
    
    const chartCtx = ctx.getContext('2d');
    if (chartInstances[canvasId]) chartInstances[canvasId].destroy();
    
    // Crear bins para el histograma
    const min = Math.min(...costs);
    const max = Math.max(...costs);
    const binCount = 15;
    const binWidth = (max - min) / binCount;
    
    const bins = Array(binCount).fill(0);
    const labels = [];
    
    // Crear etiquetas para los bins
    for (let i = 0; i < binCount; i++) {
        const binStart = min + i * binWidth;
        const binEnd = binStart + binWidth;
        labels.push(`$${binStart.toFixed(2)}-$${binEnd.toFixed(2)}`);
    }
    
    // Contar valores en cada bin
    costs.forEach(value => {
        const binIndex = Math.min(Math.floor((value - min) / binWidth), binCount - 1);
        bins[binIndex]++;
    });
    
    const options = {
        ...defaultChartOptions,
        plugins: {
            ...defaultChartOptions.plugins
        }
    };
    
    // Añadir anotaciones si el plugin está disponible
    if (Chart.annotation) {
        options.plugins.annotation = {
            annotations: {
                meanLine: {
                    type: 'line',
                    scaleID: 'x',
                    value: stats.mean,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 2,
                    label: {
                        content: `Media: $${stats.mean.toFixed(2)}`,
                        enabled: true,
                        position: 'start'
                    }
                },
                costo90Line: {
                    type: 'line',
                    scaleID: 'x',
                    value: stats.costo90,
                    borderColor: 'rgba(153, 102, 255, 1)',
                    borderWidth: 2,
                    label: {
                        content: `Costo90: $${stats.costo90.toFixed(2)}`,
                        enabled: true,
                        position: 'end'
                    }
                }
            }
        };
    }
    
    // Crear gráfico
    chartInstances[canvasId] = new Chart(chartCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: `Costo ${label}`,
                data: bins,
                backgroundColor: label === 'Línea Base' ? 'rgba(54, 162, 235, 0.6)' : 'rgba(75, 192, 192, 0.6)',
                borderColor: label === 'Línea Base' ? 'rgba(54, 162, 235, 1)' : 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: options
    });
}

// Configurar explicaciones al hacer hover
function setupExplanationHovers() {
    const explanationTriggers = document.querySelectorAll('.explanation-trigger');
    
    explanationTriggers.forEach(trigger => {
        const targetId = trigger.getAttribute('data-target');
        const explanationText = document.getElementById(targetId);
        
        if (explanationText) {
            // Mostrar explicación al hacer hover
            trigger.addEventListener('mouseenter', () => {
                explanationText.style.display = 'block';
            });
            
            // Ocultar explicación al quitar el hover
            trigger.addEventListener('mouseleave', () => {
                explanationText.style.display = 'none';
            });
        }
    });
}

// Mostrar mensaje de error
function showError(message) {
    const simulationStatus = document.getElementById('simulation-status');
    if (simulationStatus) {
        simulationStatus.textContent = message;
        simulationStatus.className = 'status-message status-error';
        simulationStatus.style.display = 'block';
    }
    
    console.error(message);
}

// Lógica del modal
function initModal() {
    const modal = document.getElementById('chart-modal');
    const modalCloseBtn = modal.querySelector('.close-button');

    function closeModal() {
        modal.style.display = 'none';
        if (chartInstances.modal) {
            chartInstances.modal.destroy();
            chartInstances.modal = null;
        }
    }

    modalCloseBtn.onclick = closeModal;
    window.onclick = (event) => {
        if (event.target === modal) {
            closeModal();
        }
    };
}

function openChartInModal(canvasId) {
    const originalChart = chartInstances[canvasId];
    if (!originalChart) return;

    const modal = document.getElementById('chart-modal');
    const modalCanvas = document.getElementById('modal-chart');
    const modalCtx = modalCanvas.getContext('2d');
    
    if (chartInstances.modal) {
        chartInstances.modal.destroy();
    }
    
    // Clonar configuración de manera segura
    const modalConfig = {
        type: originalChart.config.type,
        data: JSON.parse(JSON.stringify(originalChart.data)),
        options: JSON.parse(JSON.stringify(originalChart.config.options || {}))
    };
    
    // Asegurarse de que la estructura de plugins existe
    if (!modalConfig.options.plugins) {
        modalConfig.options.plugins = {};
    }
    
    // Añadir configuración de zoom
    modalConfig.options.plugins.zoom = {
        pan: {
            enabled: true,
            mode: 'xy'
        },
        zoom: {
            wheel: {
                enabled: true,
            },
            pinch: {
                enabled: true
            },
            mode: 'xy',
        }
    };

    chartInstances.modal = new Chart(modalCtx, modalConfig);
    modal.style.display = 'block';
} 