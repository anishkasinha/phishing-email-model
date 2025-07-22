// Configuration
const API_BASE_URL = 'http://127.0.0.1:5000'; // Your Flask API URL

// API call function
async function analyzeEmailWithAPI(emailText) {
  try {
    const response = await fetch(`${API_BASE_URL}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email_text: emailText
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}

// Function to update UI based on API response
function updateThreatIndicator(apiResponse) {
  const dot = document.getElementById("threat-indicator");
  const desc = document.getElementById("description");

  if (apiResponse.prediction === 1) {
    // Phishing detected
    dot.style.marginLeft = "130px"; // High Threat
    const confidence = Math.round(apiResponse.confidence.phishing * 100);
    desc.value = `🚨 PHISHING DETECTED: This email is likely a phishing attempt (${confidence}% confidence). Risk Level: ${apiResponse.risk_level}`;
  } else {
    // Safe email
    if (apiResponse.risk_level === "LOW") {
      dot.style.marginLeft = "0px"; // Low Threat
      const confidence = Math.round(apiResponse.confidence.safe * 100);
      desc.value = `✅ Safe Email: This email appears legitimate (${confidence}% confidence). Risk Level: ${apiResponse.risk_level}`;
    } else if (apiResponse.risk_level === "MEDIUM") {
      dot.style.marginLeft = "65px"; // Medium Threat
      const phishingConfidence = Math.round(apiResponse.confidence.phishing * 100);
      desc.value = `⚠️ Medium Risk: This email shows some suspicious patterns (${phishingConfidence}% phishing probability). Please review carefully.`;
    } else {
      dot.style.marginLeft = "0px"; // Low Threat (fallback)
      desc.value = `✅ Safe Email: This email appears legitimate.`;
    }
  }
}

// Function to show loading state
function showLoadingState() {
  const dot = document.getElementById("threat-indicator");
  const desc = document.getElementById("description");
  
  dot.style.marginLeft = "65px"; // Center position
  desc.value = "🔄 Analyzing email... Please wait.";
}

// Function to show error state
function showErrorState(error) {
  const dot = document.getElementById("threat-indicator");
  const desc = document.getElementById("description");
  
  dot.style.marginLeft = "65px"; // Center position
  desc.value = `❌ Analysis Error: ${error.message}. Please try again or check if the API server is running.`;
}

// Main event listener with API integration
document.getElementById("analyze").addEventListener("click", async () => {
  const message = document.getElementById("message").value;
  
  // Check if message is empty
  if (message.trim() === "") {
    const dot = document.getElementById("threat-indicator");
    const desc = document.getElementById("description");
    dot.style.marginLeft = "65px";
    desc.value = "Please enter or paste an email to analyze.";
    return;
  }

  // Show loading state
  showLoadingState();

  try {
    // Call the API
    const apiResponse = await analyzeEmailWithAPI(message);
    
    // Update UI with results
    updateThreatIndicator(apiResponse);
    
    // Log response for debugging
    console.log('API Response:', apiResponse);
    
  } catch (error) {
    // Handle errors (API down, network issues, etc.)
    console.error('Failed to analyze email:', error);
    
    // Fall back to simple logic if API fails
    if (error.message.includes('fetch')) {
      showErrorState({ message: 'Cannot connect to analysis service' });
      
      // Optional: Fall back to your original simple logic
      fallbackAnalysis(message.toLowerCase());
    } else {
      showErrorState(error);
    }
  }
});

// Fallback function using your original logic (optional)
function fallbackAnalysis(message) {
  const dot = document.getElementById("threat-indicator");
  const desc = document.getElementById("description");
  
  console.log('Using fallback analysis...');
  
  if (message.includes("click here") || message.includes("verify") || message.includes("urgent")) {
    dot.style.marginLeft = "130px"; // High Threat
    desc.value = "⚠️ High Threat: This email contains suspicious language (offline analysis).";
  } else if (message.includes("meeting") || message.includes("schedule") || message.includes("lunch")) {
    dot.style.marginLeft = "0px"; // Low Threat
    desc.value = "✅ Low Threat: This email appears to contain everyday communication (offline analysis).";
  } else {
    dot.style.marginLeft = "65px"; // Medium Threat
    desc.value = "⚠️ Medium Threat: This email contains unknown content (offline analysis).";
  }
}

// Optional: Check API health on page load
window.addEventListener('DOMContentLoaded', async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (response.ok) {
      const health = await response.json();
      console.log('API Health:', health);
      
      if (health.status !== 'healthy') {
        console.warn('API is not healthy:', health);
      }
    }
  } catch (error) {
    console.warn('Could not connect to API:', error.message);
  }
});