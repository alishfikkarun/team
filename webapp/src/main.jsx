import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import GiftPage from "./pages/GiftPage";
import "./index.css";

function App(){
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/gift/:slug" element={<GiftPage/>} />
        <Route path="*" element={<div className="min-h-screen bg-[#0d1117] text-white flex items-center justify-center">Open a gift link</div>} />
      </Routes>
    </BrowserRouter>
  )
}

createRoot(document.getElementById("root")).render(<App/>);
