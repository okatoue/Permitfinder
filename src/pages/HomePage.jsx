import React from 'react';
import { Link } from 'react-router-dom';
import Button from '../components/Button';
import Icon from '../components/Icon';
import { PropCard } from '../components/Card';
import Footer from '../components/Footer';

/**
 * HomePage component - converted from test.html
 * Main landing page for Scope Signals
 */
const HomePage = () => {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="py-24 md:py-28 relative text-center">
        {/* Animated Glow Effect */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] md:w-[800px] md:h-[400px] pointer-events-none">
          <div
            className="absolute inset-0 rounded-full opacity-30 blur-[100px]"
            style={{
              background: 'radial-gradient(circle, var(--accent) 0%, transparent 70%)',
              animation: 'heroGlow 4s ease-in-out infinite',
            }}
          />
        </div>

        <h1
          className="relative z-10 text-5xl md:text-[4.5rem] lg:text-[5.5rem] font-extrabold mb-8 bg-gradient-to-br from-text-primary to-text-secondary bg-clip-text text-transparent"
          style={{ lineHeight: 1.15, letterSpacing: '-2px' }}
        >
          Seattle Roofing Leads.
          <br />
          Straight To Your Inbox.
        </h1>

        {/* Keyframes for glow animation */}
        <style>{`
          @keyframes heroGlow {
            0%, 100% {
              opacity: 0.2;
              transform: scale(1);
            }
            50% {
              opacity: 0.4;
              transform: scale(1.1);
            }
          }
        `}</style>
        <p className="text-lg md:text-xl text-text-secondary max-w-[600px] mx-auto mb-10">
          We monitor city data to surface fresh opportunities <br /> No crowded marketplaces. Just actionable leads.
        </p>
        <div className="flex justify-center gap-4 flex-wrap">
          <Button variant="primary" to="/pricing">
            Check ZIP Availability
          </Button>
          <Button variant="secondary" to="/how-it-works">
            See How It Works
          </Button>
        </div>
      </section>

      {/* Value Props Section */}
      <section className="py-20 grid grid-cols-1 md:grid-cols-3 gap-6 border-b border-border-color">
        <PropCard
          icon={<Icon name="lock" size={24} />}
          title="Protected Territory"
          description="We cap the number of roofers per ZIP code to ensure your leads stay valuable. Once a ZIP is full, it's locked."
        />
        <PropCard
          icon={<Icon name="lightning" size={24} />}
          title="Real-Time Intel"
          description="Daily updates from Seattle public records. Catch reroof permits and code violations before the competition knows they exist."
        />
        <PropCard
          icon={<Icon name="download" size={24} />}
          title="CRM Ready"
          description="Get a morning email digest, a searchable dashboard, and one-click CSV exports for your workflow."
        />
      </section>

      {/* Product Reveal Section */}
      <section className="py-24 flex flex-col items-center text-center">
        <h2 className="text-3xl md:text-4xl font-bold text-text-primary mb-3">
          Built for Speed
        </h2>
        <p className="text-text-secondary mb-8">
          From city database to your inbox in minutes.
        </p>

        {/* Mockup Container */}
        <div className="relative w-full max-w-[800px] h-[300px] md:h-[450px] mt-8">
          {/* Dashboard Mockup */}
          <div
            className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full bg-bg-card border border-border-color rounded-xl shadow-[0_40px_80px_rgba(0,0,0,0.6)] p-5 overflow-hidden"
            style={{ transform: 'translateX(-50%) perspective(1000px) rotateX(10deg)' }}
          >
            <div className="flex gap-4 h-full">
              {/* Sidebar */}
              <div className="w-[18%] h-full bg-[#131821] rounded-md border border-border-color hidden md:block" />

              {/* Content */}
              <div className="flex-1 flex flex-col gap-4">
                {/* Map */}
                <div
                  className="flex-1 bg-[#11151d] rounded-md border border-border-color relative"
                  style={{
                    backgroundImage: 'radial-gradient(var(--border) 1px, transparent 1px)',
                    backgroundSize: '20px 20px',
                  }}
                >
                  {/* Map Pins */}
                  <MapPin style={{ top: '30%', left: '40%' }} />
                  <MapPin style={{ top: '50%', left: '60%' }} />
                  <MapPin style={{ top: '20%', left: '70%' }} />
                </div>

                {/* List */}
                <div className="h-[30%] bg-[#131821] rounded-md border border-border-color" />
              </div>
            </div>
          </div>

          {/* Floating Notification Toast */}
          <div className="hidden md:block absolute top-10 right-[-20px] w-[260px] bg-bg-card text-text-primary border border-border-color border-l-[3px] border-l-status-amber rounded-md p-4 shadow-[0_15px_30px_rgba(0,0,0,0.4)] text-sm rotate-3 z-10">
            <strong className="text-text-primary">New Alert: 98103</strong>
            <br />
            <span className="text-text-secondary">3 Reroof Permits detected.</span>
          </div>

          {/* Floating Card */}
          <div className="hidden md:block absolute bottom-[-30px] left-10 w-[320px] bg-[#1A222E] border border-border-color rounded-lg p-5 shadow-[0_20px_40px_rgba(0,0,0,0.5)] -rotate-3">
            <span className="text-[0.7rem] font-bold text-accent border border-accent px-1.5 py-0.5 rounded inline-block mb-3">
              REROOF PERMIT
            </span>
            <div className="font-semibold text-text-primary mb-1">
              2401 3rd Ave, Seattle
            </div>
            <div className="text-[0.8rem] text-text-muted">
              Issued: Today, 9:00 AM
            </div>
            <div className="mt-4 flex gap-2.5">
              <div className="flex-1 h-2 bg-border-color rounded" />
              <div className="w-[30%] h-2 bg-border-color rounded" />
            </div>
          </div>
        </div>
      </section>

      {/* Features Split Section */}
      <section className="py-24 grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
        <div>
          <h2 className="text-3xl md:text-4xl font-bold text-text-primary mb-4">
            Everything you need to dominate.
          </h2>
          <p className="text-text-secondary mb-8">
            Stop wasting time on dead leads. Get data that actually converts.
          </p>

          <ul className="space-y-4">
            <FeatureItem>Daily or Weekly Email Digests</FeatureItem>
            <FeatureItem>Full Dashboard Access</FeatureItem>
            <FeatureItem>Filter by Permit Type & Urgency</FeatureItem>
            <FeatureItem>CSV / Excel Exports</FeatureItem>
            <FeatureItem highlight>ZIP Seat Protection</FeatureItem>
          </ul>

          <div className="inline-block mt-6 px-4 py-2 bg-bg-card border border-border-color rounded-full text-[0.8rem] text-text-muted">
            Source: Seattle Dept. of Construction & Inspections
          </div>
        </div>

        {/* CSV Mockup */}
        <div className="bg-bg-card border border-border-color rounded-xl p-8 font-mono text-[0.85rem] text-text-secondary">
          <div className="text-text-primary border-b border-border-color pb-3 mb-3">
            Address, Permit_Type, Date, Est_Value
          </div>
          <div className="opacity-80 space-y-2">
            <div>421 Elm St, Reroof, 2026-01-24, <span className="text-accent">$15,000</span></div>
            <div>809 Oak Rd, Repair, 2026-01-24, <span className="text-accent">$5,200</span></div>
            <div>102 Pine Wy, Reroof, 2026-01-23, <span className="text-accent">$22,500</span></div>
            <div>550 West Ave, Solar, 2026-01-23, <span className="text-accent">$30,000</span></div>
          </div>
          <div className="mt-5 text-status-blue cursor-pointer hover:underline">
            ⬇ Download Sample.csv
          </div>
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="mb-24 rounded-2xl border border-border-color p-12 md:p-20 text-center bg-gradient-radial from-bg-card to-bg-color">
        <h2 className="text-2xl md:text-3xl font-bold text-text-primary mb-5">
          Don't let your competitors lock down your ZIPs.
        </h2>
        <p className="text-text-secondary mb-8">
          Check which Seattle territories are still available for exclusive monitoring.
        </p>
        <Button variant="primary" to="/pricing">
          Check Coverage & Pricing
        </Button>
      </section>

      <Footer />
    </div>
  );
};

/**
 * Map Pin component for the dashboard mockup
 */
const MapPin = ({ style }) => (
  <div
    className="absolute w-3 h-3 bg-accent rounded-full shadow-[0_0_12px_var(--accent)]"
    style={style}
  >
    <div className="absolute -top-1 -left-1 w-5 h-5 border border-accent rounded-full opacity-50" />
  </div>
);

/**
 * Feature Item component for the features list
 */
const FeatureItem = ({ children, highlight = false }) => (
  <li className="flex items-center gap-3 text-lg text-text-secondary">
    <span className="text-accent">✓</span>
    {highlight ? <strong>{children}</strong> : children}
  </li>
);

export default HomePage;
