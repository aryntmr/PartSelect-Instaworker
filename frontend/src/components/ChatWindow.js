import React, { useState, useEffect, useRef } from "react";
import "./ChatWindow.css";
import { getAIMessage } from "../api/api";
import { marked } from "marked";
import PartCard from "./PartCard";

function ChatWindow() {

  const defaultMessage = [{
    role: "assistant",
    content: "Hi, how can I help you today?"
  }];

  const [messages, setMessages] = useState(defaultMessage);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
      scrollToBottom();
  }, [messages]);

  const handleSend = async (inputText) => {
    if (inputText.trim() !== "" && !isLoading) {
      // Set user message
      setMessages(prevMessages => [...prevMessages, { role: "user", content: inputText }]);
      setInput("");
      setIsLoading(true);

      try {
        // Call API & set assistant message
        const newMessage = await getAIMessage(inputText);
        setMessages(prevMessages => [...prevMessages, newMessage]);
      } catch (error) {
        console.error('Error in handleSend:', error);
        // Add error message to chat
        setMessages(prevMessages => [...prevMessages, {
          role: "assistant",
          content: "An error occurred while processing your request. Please try again.",
          products: []
        }]);
      } finally {
        setIsLoading(false);
      }
    }
  };

  return (
      <div className="messages-container">
          {messages.map((message, index) => (
              <div key={index} className={`${message.role}-message-container`}>
                  {message.content && (
                      <div className={`message ${message.role}-message`}>
                          <div dangerouslySetInnerHTML={{__html: marked(message.content).replace(/<p>|<\/p>/g, "")}}></div>
                      </div>
                  )}
                  {message.role === "assistant" && message.products && message.products.length > 0 && (
                      <div className="product-cards-container">
                          {message.products.map((product) => (
                              <PartCard key={product.part_id} product={product} />
                          ))}
                      </div>
                  )}
              </div>
          ))}
          <div ref={messagesEndRef} />
          {isLoading && (
            <div className="assistant-message-container">
              <div className="message assistant-message">
                <div>Searching...</div>
              </div>
            </div>
          )}
          <div className="input-area">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
              onKeyPress={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  handleSend(input);
                  e.preventDefault();
                }
              }}
              rows="3"
            />
            <button 
              className="send-button" 
              onClick={() => handleSend(input)}
              disabled={isLoading || input.trim() === ""}
            >
              {isLoading ? "Sending..." : "Send"}
            </button>
          </div>
      </div>
);
}

export default ChatWindow;
