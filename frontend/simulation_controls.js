// Simulation Controls Handler
// Manages pause/resume and reset functionality

import { socket } from './socket_handler.js';

let isPaused = false;

function initSimulationControls() {
    const pauseResumeBtn = document.getElementById('pauseResumeBtn');
    const resetBtn = document.getElementById('resetBtn');
    const controlsContainer = document.getElementById('simulationControls');
    
    if (pauseResumeBtn) {
        pauseResumeBtn.addEventListener('click', togglePause);
    }
    
    if (resetBtn) {
        resetBtn.addEventListener('click', resetSimulation);
    }
    
    // Listen for simulation events
    socket.on('simulation_started', () => {
        isPaused = false;
        const pauseResumeBtn = document.getElementById('pauseResumeBtn');
        if (pauseResumeBtn) pauseResumeBtn.textContent = 'PAUSE';
        showControls();
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
        showOpeningScreen();
    });
    
    socket.on('game_over', () => {
        // Optionally hide or disable controls on game over
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

function showOpeningScreen() {
    const openingScreen = document.getElementById('openingScreen');
    if (openingScreen) {
        openingScreen.classList.remove('hidden');
        openingScreen.style.opacity = '1';
    }
    
    // Re-enable country buttons
    const buttons = document.querySelectorAll('.country-btn');
    buttons.forEach(btn => {
        btn.disabled = false;
        btn.classList.remove('selected', 'deploying');
        btn.textContent = btn.dataset.country;
    });
}

async function togglePause() {
    const pauseResumeBtn = document.getElementById('pauseResumeBtn');
    if (!pauseResumeBtn) return;
    
    pauseResumeBtn.disabled = true;
    
    // Immediately update button for better UX
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
        // Revert on error
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
    
    // Confirm reset
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
            // Reset will be handled by socket event
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
    
    // Reset stats display
    document.getElementById('stat-utility').innerText = '--';
    document.getElementById('stat-infected').innerText = '--';
    document.getElementById('stat-deaths').innerText = '--';
    document.getElementById('bar-utility').style.width = '0%';
    document.getElementById('bar-infected').style.width = '0%';
    document.getElementById('footer-tick').innerText = '--';
    document.getElementById('footer-vac').innerText = '--';
    document.getElementById('footer-evo').innerText = '--';
    
    // Clear country cards
    const countriesList = document.getElementById('countriesList');
    if (countriesList) countriesList.innerHTML = '';
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initSimulationControls);

export { initSimulationControls, showControls, hideControls };
