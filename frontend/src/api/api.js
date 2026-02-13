// Backend API base URL
const API_BASE_URL = 'http://localhost:8000';

export const getAIMessage = async (userQuery, conversationHistory = []) => {
  try {
    // Call backend chat endpoint with conversation history
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: userQuery,
        history: conversationHistory
      })
    });

    // Check if response is ok
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    // Parse JSON response
    const data = await response.json();

    // Return assistant message with reply text and products
    const message = {
      role: "assistant",
      content: data.reply || "I couldn't process your request. Please try again.",
      products: data.metadata?.products || []
    };

    return message;

  } catch (error) {
    console.error('Error calling backend API:', error);
    
    // Return error message to user
    const errorMessage = {
      role: "assistant",
      content: "Sorry, I'm having trouble connecting to the server. Please make sure the backend is running on port 8000.",
      products: []  // Empty products array
    };

    return errorMessage;
  }
};
