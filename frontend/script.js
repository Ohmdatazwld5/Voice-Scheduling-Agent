let recognition;

// Detect environment - use relative URL for production
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
  ? 'http://127.0.0.1:8000' 
  : '';

function startListening() {
  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.continuous = false;

  recognition.onresult = async (event) => {
    const transcript = event.results[0][0].transcript;
    document.getElementById("output").innerText = transcript;

    // Send transcript to backend
    await fetch(`${API_BASE}/api/schedule`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ transcript }),
    });
  };

  recognition.start();
}

async function scheduleFromVoice(conversation) {
  try {
    result.style.display = "block";
    result.className = "";
    result.innerHTML = "<p>⏳ Processing your request...</p>";
    status.textContent = "Processing...";
    status.style.color = "#ff9800";

    console.log("Sending to backend:", conversation);

    const response = await fetch(`${API_BASE}/api/schedule`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        conversation: conversation,
        access_token: "",
      }),
    });

    // Log the response status
    console.log("Response status:", response.status);

    const data = await response.json();
    console.log("Backend response:", data);

    // Check for validation errors
    if (response.status === 422) {
      result.className = "error";
      result.innerHTML = `<p><strong>❌ Validation Error:</strong></p><pre>${JSON.stringify(
        data,
        null,
        2
      )}</pre>`;
      status.textContent = "Validation error";
      status.style.color = "red";
      return;
    }

    if (data.error) {
      result.className = "error";
      result.innerHTML = `<p><strong>❌ Error:</strong> ${data.error}</p>`;
      status.textContent = "Error";
      status.style.color = "red";
    } else {
      result.className = "success";
      result.innerHTML = `
                <h3>✅ Meeting Details Extracted!</h3>
                <div class="meeting-details">
                    <p><strong>👤 Name:</strong> ${data.meeting.name}</p>
                    <p><strong>📅 Date:</strong> ${data.meeting.date}</p>
                    <p><strong>🕐 Time:</strong> ${data.meeting.time}</p>
                    <p><strong>📋 Title:</strong> ${data.meeting.title || "Meeting"}</p>
                </div>
                <p style="margin-top: 15px; font-size: 14px;"><em>💡 ${data.message}</em></p>
            `;
      status.textContent = "Success!";
      status.style.color = "#4CAF50";
    }
  } catch (error) {
    console.error("Fetch error:", error);
    result.style.display = "block";
    result.className = "error";
    result.innerHTML = `
            <p><strong>❌ Network Error:</strong> ${error.message}</p>
            <p style="margin-top: 10px; font-size: 14px;">Make sure the backend server is running at http://127.0.0.1:8000</p>
        `;
    status.textContent = "Network error";
    status.style.color = "red";
  }
}
