import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import "../tailwind.css";

import { ChatBotUi } from "./screens/ChatBotUi";
import UnderDevelopment from "./pages/UnderDevelopment";

createRoot(document.getElementById("app") as HTMLElement).render(
  <StrictMode>
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <Routes>
        <Route path="/" element={<ChatBotUi />} />
        <Route path="/under-development" element={<UnderDevelopment />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
