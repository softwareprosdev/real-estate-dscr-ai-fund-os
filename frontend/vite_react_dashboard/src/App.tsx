import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import UnderwritingPage from "./pages/UnderwritingPage";
import DealDecisionPage from "./pages/DealDecisionPage";
import BiddingPage from "./pages/BiddingPage";
import PortfolioPage from "./pages/PortfolioPage";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        <nav className="bg-gray-900 border-b border-gray-700 px-6 py-3 flex items-center gap-6">
          <span className="text-green-400 font-bold text-lg tracking-tight">DSCR AI FUND OS</span>
          {[
            { to: "/", label: "Underwriting" },
            { to: "/decision", label: "Decision" },
            { to: "/bidding", label: "Bidding" },
            { to: "/portfolio", label: "Portfolio" },
          ].map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `text-sm px-3 py-1 rounded ${isActive ? "bg-green-600 text-white" : "text-gray-400 hover:text-white"}`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
        <main className="flex-1 p-6">
          <Routes>
            <Route path="/" element={<UnderwritingPage />} />
            <Route path="/decision" element={<DealDecisionPage />} />
            <Route path="/bidding" element={<BiddingPage />} />
            <Route path="/portfolio" element={<PortfolioPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
