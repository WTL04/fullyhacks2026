// Simulation Controls Handler
// Manages pause/resume, reset functionality, and Virus Shop

import { socket } from './socket_handler.js';
import { showOutbreakReport } from './opening_screen.js';

let isPaused = false;
let lastState = null;

function initSimulationControls() {
    const pauseResumeBtn = document.getElementById('pauseResumeBtn');
    const resetBtn = document.getElementById('resetBtn');
    const controlsContainer = document.getElementById('simulationControls');
    
    // Virus Shop elements
    const virusShopBtn = document.getElementById('virusShopBtn');
    const virusShopPopup = document.getElementById('virusShopPopup');
    const closeShopBtn = document.getElementById('closeShopBtn');
    const jumpBtn = document.getElementById('jumpBtn');
    const mutateBtn = document.getElementById('mutateBtn');
    const jumpCountrySelect = document.getElementById('jumpCountrySelect');
    const shopResult = document.getElementById('shopResult');
    const shopEvoValue = document.getElementById('shop-evo-value');

    if (pauseResumeBtn) {
        pauseResumeBtn.addEventListener('click', togglePause);
    }
    
    if (resetBtn) {
        resetBtn.addEventListener('click', resetSimulation);
    }

    if (virusShopBtn) {
        virusShopBtn.addEventListener('click', () => {
            populateCountrySelect(jumpCountrySelect);
            if (shopEvoValue && lastState) {
                shopEvoValue.innerText = lastState.evolution_points.toFixed(1);
            }
            virusShopPopup.classList.remove('hidden');
            shopResult.innerText = '';
            shopResult.className = 'shop-result';
        });
    }

    if (closeShopBtn) {
        closeShopBtn.addEventListener('click', () => {
            virusShopPopup.classList.add('hidden');
        });
    }

    if (jumpBtn) {
        jumpBtn.addEventListener('click', () => {
            const target = jumpCountrySelect.value;
            if (!target) return;
            socket.emit('user_action', { type: 'virus_jump', target: target });
        });
    }

    if (mutateBtn) {
        mutateBtn.addEventListener('click', () => {
            socket.emit('user_action', { type: 'force_mutation', target: '' });
        });
    }
    
    // Listen for simulation events
    socket.on('simulation_started', () => {
        isPaused = false;
        const pauseResumeBtn = document.getElementById('pauseResumeBtn');
        if (pauseResumeBtn) pauseResumeBtn.textContent = 'PAUSE';
        showControls();
    });

    socket.on('action_results', (results) => {
        if (virusShopPopup && !virusShopPopup.classList.contains('hidden')) {
            const result = results[0];
            if (result) {
                shopResult.innerText = result.message;
                shopResult.className = 'shop-result ' + (result.status === 'success' ? 'success' : 'error');
            }
        }
    });
    
    socket.on('simulation_paused', (data) => {
        isPaused = data.paused;
        updatePauseButton();
    });
    
    socket.on('simulation_reset', () => {
        hideControls();
        isPaused = false;
        const pauseResumeBtn = document.getElementById('pauseResumeBtn');
        if (pauseResumeBtn) pauseResumeBtn.textContent = 'PAUSE';
        showOutbreakReport();
    });
    
    socket.on('game_over', () => {
        // Optionally hide or disable controls on game over
    });

    socket.on('state_update', (data) => {
        lastState = data;
        const shopEvoValue = document.getElementById('shop-evo-value');
        if (shopEvoValue) {
            shopEvoValue.innerText = data.evolution_points.toFixed(1);
        }
    });
}

function showControls() {
    const controls = document.getElementById('simulationControls');
    if (controls) {
        controls.classList.remove('hidden');
    }
}

function hideControls() {
    const controls = document.getElementById('simulationControls');
    if (controls) {
        controls.classList.add('hidden');
    }
}

async function togglePause() {
    const pauseResumeBtn = document.getElementById('pauseResumeBtn');
    if (!pauseResumeBtn) return;
    
    pauseResumeBtn.disabled = true;
    isPaused = !isPaused;
    updatePauseButton();
    
    try {
        const endpoint = isPaused ? '/pause' : '/resume';
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const result = await response.json();
        if (result.status === 'success') {
            isPaused = result.paused;
        }
    } catch (error) {
        console.error('Toggle pause error:', error);
        isPaused = !isPaused;
        updatePauseButton();
    } finally {
        pauseResumeBtn.disabled = false;
    }
}

function updatePauseButton() {
    const pauseResumeBtn = document.getElementById('pauseResumeBtn');
    if (!pauseResumeBtn) return;
    if (isPaused) {
        pauseResumeBtn.textContent = 'RESUME';
        pauseResumeBtn.style.background = 'rgba(34, 197, 94, 0.2)';
        pauseResumeBtn.style.borderColor = '#22c55e';
        pauseResumeBtn.style.color = '#22c55e';
    } else {
        pauseResumeBtn.textContent = 'PAUSE';
        pauseResumeBtn.style.background = 'rgba(234, 179, 8, 0.2)';
        pauseResumeBtn.style.borderColor = '#eab308';
        pauseResumeBtn.style.color = '#eab308';
    }
}

async function resetSimulation() {
    const resetBtn = document.getElementById('resetBtn');
    if (!resetBtn) return;
    if (!confirm('Are you sure you want to reset the simulation?')) {
        return;
    }
    resetBtn.disabled = true;
    try {
        const response = await fetch('/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const result = await response.json();
        if (result.status === 'success') {
            clearLogs();
        }
    } catch (error) {
        console.error('Reset error:', error);
    } finally {
        resetBtn.disabled = false;
    }
}

function clearLogs() {
    const logFeed = document.getElementById('log-feed');
    const virusFeed = document.getElementById('virus-feed');
    if (logFeed) logFeed.innerHTML = '';
    if (virusFeed) virusFeed.innerHTML = '';
    document.getElementById('stat-utility').innerText = '--';
    document.getElementById('stat-infected').innerText = '--';
    document.getElementById('stat-deaths').innerText = '--';
    document.getElementById('bar-utility').style.width = '0%';
    document.getElementById('bar-infected').style.width = '0%';
    document.getElementById('footer-day').innerText = '--';
    document.getElementById('footer-vac').innerText = '--';
    document.getElementById('footer-evo').innerText = '--';
    const countriesList = document.getElementById('countriesList');
    if (countriesList) countriesList.innerHTML = '';
}

function populateCountrySelect(select) {
    if (!lastState || !lastState.countries) return;
    select.innerHTML = '';
    const countries = Object.keys(lastState.countries).sort();
    countries.forEach(country => {
        const option = document.createElement('option');
        option.value = country;
        option.textContent = country;
        select.appendChild(option);
    });
}

initSimulationControls();

export { initSimulationControls, showControls, hideControls };

