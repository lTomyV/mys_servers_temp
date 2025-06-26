// Variables globales
let simulationRunning = false;
let statusCheckInterval = null;
let chartInstances = {};

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
    updateCharts(data);
    
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

// Actualizar gráficos
function updateCharts(data) {
    // Actualizar gráfico de diagnóstico de randomización
    if (data.randomization_diagnostic) {
        const randomizationImg = document.getElementById('randomization-diagnostic');
        if (randomizationImg) {
            randomizationImg.src = data.randomization_diagnostic;
        }
    }
    
    // Actualizar gráfico de distribución de temperaturas horarias
    if (data.hourly_temp_distribution) {
        const tempDistImg = document.getElementById('temperature-distribution');
        if (tempDistImg) {
            tempDistImg.src = data.hourly_temp_distribution;
        }
    }
    
    // Actualizar gráficos de histogramas de costos
    updateHistograms(data);
    
    // Actualizar gráfico de curvas COP
    if (data.cop_curves) {
        const copCurvesImg = document.getElementById('cop-curves');
        if (copCurvesImg) {
            copCurvesImg.src = data.cop_curves;
        }
    }
}

// Actualizar histogramas de costos
function updateHistograms(data) {
    // Histograma Línea Base
    if (data.costs_baseline) {
        const baselineCanvas = document.getElementById('baseline-histogram');
        if (baselineCanvas) {
            // Destruir gráfico anterior si existe
            if (chartInstances.baseline) {
                chartInstances.baseline.destroy();
            }
            
            // Crear nuevo histograma
            const ctx = baselineCanvas.getContext('2d');
            chartInstances.baseline = createHistogram(
                ctx, 
                data.costs_baseline, 
                'Distribución de Costos - Línea Base',
                data.baseline_stats.mean,
                data.baseline_stats.costo90
            );
        }
    }
    
    // Histograma Optimizado
    if (data.costs_optimized) {
        const optimizedCanvas = document.getElementById('optimized-histogram');
        if (optimizedCanvas) {
            // Destruir gráfico anterior si existe
            if (chartInstances.optimized) {
                chartInstances.optimized.destroy();
            }
            
            // Crear nuevo histograma
            const ctx = optimizedCanvas.getContext('2d');
            chartInstances.optimized = createHistogram(
                ctx, 
                data.costs_optimized, 
                'Distribución de Costos - Optimizado',
                data.optimized_stats.mean,
                data.optimized_stats.costo90
            );
        }
    }
}

// Crear histograma
function createHistogram(ctx, data, label, mean, percentile90) {
    // Calcular bins para el histograma
    const min = Math.min(...data);
    const max = Math.max(...data);
    const binWidth = (max - min) / 15;
    const bins = Array(15).fill(0);
    
    // Contar valores en cada bin
    data.forEach(value => {
        const binIndex = Math.min(Math.floor((value - min) / binWidth), bins.length - 1);
        bins[binIndex]++;
    });
    
    // Normalizar bins para obtener densidad de probabilidad
    const totalSamples = data.length;
    const normalizedBins = bins.map(count => count / (totalSamples * binWidth));
    
    // Crear etiquetas para el eje x (centros de los bins)
    const labels = Array(15).fill(0).map((_, i) => (min + (i + 0.5) * binWidth).toFixed(2));
    
    // Crear gráfico
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Densidad de Probabilidad',
                data: normalizedBins,
                backgroundColor: 'rgba(75, 192, 192, 0.6)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Costo Mensual ($)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Densidad de Probabilidad'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: label
                },
                annotation: {
                    annotations: {
                        meanLine: {
                            type: 'line',
                            xMin: mean,
                            xMax: mean,
                            borderColor: 'red',
                            borderWidth: 2,
                            label: {
                                enabled: true,
                                content: `Media: $${mean.toFixed(2)}`,
                                position: 'start'
                            }
                        },
                        percentileLine: {
                            type: 'line',
                            xMin: percentile90,
                            xMax: percentile90,
                            borderColor: 'purple',
                            borderWidth: 2,
                            label: {
                                enabled: true,
                                content: `Costo90: $${percentile90.toFixed(2)}`,
                                position: 'end'
                            }
                        }
                    }
                }
            }
        }
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