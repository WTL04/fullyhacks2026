// Opening Screen Handler
// Manages country selection and virus story generation

const COUNTRIES = [
    'USA', 'Canada', 'Mexico', 'Brazil', 
    'Argentina', 'Chile', 'Colombia', 'Venezuela'
];

// Initialize opening screen
function initOpeningScreen() {
    const countryButtonsContainer = document.getElementById('countryButtons');
    
    // Create country buttons
    COUNTRIES.forEach(country => {
        const btn = document.createElement('button');
        btn.className = 'country-btn';
        btn.textContent = country;
        btn.dataset.country = country;
        btn.addEventListener('click', () => deployVirus(country, btn));
        countryButtonsContainer.appendChild(btn);
    });
    
    // Generate virus story
    generateVirusStory();
}

// Deploy virus to selected country
async function deployVirus(country, buttonElement) {
    // Disable all buttons and show deploying state
    const allButtons = document.querySelectorAll('.country-btn');
    allButtons.forEach(btn => btn.disabled = true);
    buttonElement.classList.add('deploying');
    buttonElement.textContent = 'DEPLOYING...';
    
    try {
        const response = await fetch('/deploy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ country })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            // Hide opening screen with fade
            const openingScreen = document.getElementById('openingScreen');
            openingScreen.style.transition = 'opacity 0.5s ease';
            openingScreen.style.opacity = '0';
            setTimeout(() => {
                openingScreen.classList.add('hidden');
            }, 500);
        } else {
            // Re-enable buttons on failure
            allButtons.forEach(btn => btn.disabled = false);
            buttonElement.classList.remove('deploying');
            buttonElement.textContent = country;
            alert(`Failed to deploy: ${result.message}`);
        }
    } catch (error) {
        console.error('Deploy error:', error);
        allButtons.forEach(btn => btn.disabled = false);
        buttonElement.classList.remove('deploying');
        buttonElement.textContent = country;
        alert('Network error. Please try again.');
    }
}

// Generate virus story using GenAI
async function generateVirusStory() {
    const storyContainer = document.getElementById('virusStory');
    
    try {
        const response = await fetch('/generate-story', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            storyContainer.innerHTML = `<p>${data.story}</p>`;
        } else {
            // Fallback to default story
            setDefaultStory(storyContainer);
        }
    } catch (error) {
        console.error('Story generation error:', error);
        // Fallback to default story
        setDefaultStory(storyContainer);
    }
}

function setDefaultStory(container) {
    const stories = [
        "ORIGIN REPORT: A novel pathogen has been detected in deep-sea research samples. Marine biologists discovered the organism in hydrothermal vents 3,000 meters below sea level. Initial analysis suggests extreme adaptability to hostile environments. Containment protocols are being established.",
        "OUTBREAK ALERT: Unusual viral signatures detected in coastal fishing communities. The pathogen appears to have originated from deep ocean ecosystems, possibly disturbed by seismic activity. Early symptoms mimic common flu but progress rapidly. Global health authorities are monitoring closely.",
        "CLASSIFIED BRIEFING: Project ABYSS has confirmed the release of an engineered pathogen. Originally designed for deep-sea bioremediation, the organism has mutated beyond containment parameters. Cross-species transmission capability confirmed. Immediate action required."
    ];
    
    const randomStory = stories[Math.floor(Math.random() * stories.length)];
    container.innerHTML = `<p>${randomStory}</p>`;
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initOpeningScreen);

export { initOpeningScreen };
