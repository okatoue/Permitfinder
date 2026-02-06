import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import PricingPage from './pages/PricingPage';
import HowItWorksPage from './pages/HowItWorksPage';
import ContactPage from './pages/ContactPage';
import PermitsPage from './pages/PermitsPage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="pricing" element={<PricingPage />} />
          <Route path="how-it-works" element={<HowItWorksPage />} />
          <Route path="contact" element={<ContactPage />} />
          <Route path="permits" element={<PermitsPage />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
