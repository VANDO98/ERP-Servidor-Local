import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { BrowserRouter } from 'react-router-dom'

const rootElement = document.getElementById('root');
if (!rootElement) {
    console.error("FATAL: Root element not found!");
    document.body.innerHTML = '<div style="color: red; font-size: 20px; padding: 20px;">FATAL: Root element id="root" not found in index.html</div>';
} else {
    try {
        console.log("Mounting React Application...");
        ReactDOM.createRoot(rootElement).render(
            <React.StrictMode>
                <BrowserRouter>
                    <App />
                </BrowserRouter>
            </React.StrictMode>,
        )
        console.log("React Application Mounted Successfully.");
    } catch (err) {
        console.error("FATAL: React Crash during mount:", err);
        rootElement.innerHTML = `<div style="color: red; padding: 20px;">
      <h1>Application Crashed</h1>
      <pre>${err.message}\n${err.stack}</pre>
    </div>`;
    }
}
