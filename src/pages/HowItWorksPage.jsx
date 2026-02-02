import React from 'react';
import { Link } from 'react-router-dom';
import Footer from '../components/Footer';

/**
 * HowItWorksPage component - converted from howitworks.html
 * Explains the product workflow and lead anatomy
 */
const HowItWorksPage = () => {
  const steps = [
    {
      number: 1,
      title: 'Select Zones',
      description:
        'Pick your Seattle ZIP codes. Seats are strictly limited (max 2) to prevent overcrowding.',
    },
    {
      number: 2,
      title: 'We Track Signals',
      description: (
        <>
          We monitor city data 24/7 for <span className="text-accent font-semibold">Reroof Permits</span> and{' '}
          <span className="text-accent font-semibold">Leak Inspections</span>.
        </>
      ),
    },
    {
      number: 3,
      title: 'Get Digests',
      description:
        'Receive a Daily or Weekly email summary. Log in to your dashboard to sort and manage leads.',
    },
    {
      number: 4,
      title: 'Export & Close',
      description:
        'Download a CSV instantly to import data into your CRM, dialer, or marketing workflow.',
    },
  ];

  const leadFeatures = [
    {
      title: 'Address + ZIP',
      description: 'Validated location within your territory.',
    },
    {
      title: 'Lead Tags',
      description: 'Instant context (e.g., Permit Type, Violation).',
    },
    {
      title: 'Date + Notes',
      description: 'When was the permit issued? What did the inspector write?',
    },
    {
      title: 'Source Link',
      description: 'Direct link back to the official city record for verification.',
    },
    {
      title: 'Score',
      description: 'A simple rating to help you prioritize high-intent jobs.',
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Page Header */}
      <header className="max-w-[700px] mx-auto text-center py-16 mb-8">
        <h1 className="text-4xl md:text-[2.5rem] font-bold mb-4 bg-gradient-to-r from-white to-[#a1a1aa] bg-clip-text text-transparent">
          From Public Data to
          <br />
          Private Pipeline.
        </h1>
        <p className="text-xl text-text-secondary">
          We turn city noise into actionable signals for your roofing business.
        </p>
      </header>

      {/* Process Steps - Horizontal Layout */}
      <div className="relative mb-28">
        {/* Horizontal Connecting Line */}
        <div
          className="hidden md:block absolute top-6 left-0 right-0 h-0.5 z-0"
          style={{
            background: 'linear-gradient(to right, var(--accent) 0%, var(--border) 100%)',
          }}
        />

        {/* Steps Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 md:gap-6">
          {steps.map((step) => (
            <StepCard key={step.number} step={step} />
          ))}
        </div>
      </div>

      {/* Lead Anatomy Section */}
      <section
        className="border-t border-b border-border-color py-20 mb-20 -mx-6 px-6"
        style={{
          background: 'radial-gradient(circle at center, #131821 0%, var(--bg-color) 100%)',
        }}
      >
        <div className="max-w-[900px] mx-auto">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-text-primary mb-2">
              What counts as a "Lead?"
            </h2>
            <p className="text-text-secondary">
              A lead is a unique address that matches one or more signals we track.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
            {/* Feature List */}
            <div>
              <h3 className="text-text-primary font-semibold mb-6">
                What you'll see on each lead:
              </h3>
              <ul className="space-y-5">
                {leadFeatures.map((feature, index) => (
                  <li key={index} className="flex gap-3 items-start text-text-secondary">
                    <div className="w-2 h-2 bg-accent rounded-full mt-2 flex-shrink-0" />
                    <div>
                      <strong>{feature.title}:</strong> {feature.description}
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            {/* Lead Card Mockup */}
            <LeadCardMockup />
          </div>
        </div>
      </section>

      {/* Data Transparency Note */}
      <div className="max-w-[600px] mx-auto mb-20 bg-[rgba(46,234,122,0.05)] border border-[rgba(46,234,122,0.1)] rounded-lg p-6 text-center">
        <h4 className="text-text-primary font-semibold mb-2">Data Transparency</h4>
        <p className="text-[0.9rem] text-text-secondary">
          We use publicly available city data and clearly show where each lead came from. We do not
          sell private homeowner phone numbers; we provide the public address and permit context so
          you can reach out via mail or door-knocking.
        </p>
      </div>

      <Footer />
    </div>
  );
};

/**
 * Step Card component for horizontal process layout
 */
const StepCard = ({ step }) => {
  return (
    <div className="relative z-10 group flex flex-col items-center text-center">
      {/* Step Circle */}
      <div
        className="w-12 h-12 aspect-square flex-shrink-0 bg-bg-card border-2 border-border-color rounded-full flex items-center justify-center text-text-muted font-bold text-xl shadow-[0_0_0_8px_var(--bg-color)] transition-all duration-200 group-hover:border-accent group-hover:text-accent group-hover:shadow-[0_0_15px_rgba(46,234,122,0.2),0_0_0_8px_var(--bg-color)] mb-6"
      >
        {step.number}
      </div>

      {/* Step Content */}
      <div className="bg-bg-card border border-border-color rounded-xl p-5 md:p-6 transition-transform duration-200 group-hover:-translate-y-1 h-full">
        <h3 className="text-lg font-bold text-text-primary mb-3">{step.title}</h3>
        <p className="text-text-secondary text-sm leading-relaxed">{step.description}</p>
      </div>
    </div>
  );
};

/**
 * Lead Card Mockup component
 */
const LeadCardMockup = () => {
  return (
    <div className="bg-bg-card border border-border-color rounded-xl p-6 shadow-[0_20px_50px_rgba(0,0,0,0.5)] relative">
      {/* Preview Label */}
      <div className="absolute -top-3 right-5 bg-bg-color px-2 text-text-muted text-[0.8rem] tracking-wider">
        PREVIEW
      </div>

      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div className="text-lg font-bold text-text-primary">2401 3rd Ave, Seattle 98121</div>
        <div className="bg-[rgba(46,234,122,0.1)] text-accent border border-accent px-2 py-1 rounded text-[0.8rem] font-bold">
          95
        </div>
      </div>

      {/* Tags */}
      <div className="flex gap-2 mb-4">
        <span className="text-[0.75rem] px-3 py-1 rounded-full bg-[rgba(239,68,68,0.15)] text-status-red border border-[rgba(239,68,68,0.3)]">
          Leak Reported
        </span>
        <span className="text-[0.75rem] px-3 py-1 rounded-full bg-[rgba(96,165,250,0.15)] text-status-blue border border-[rgba(96,165,250,0.3)]">
          Pending Inspection
        </span>
      </div>

      {/* Snippet */}
      <div className="text-[0.9rem] text-text-muted mb-4 p-3 bg-[rgba(0,0,0,0.2)] rounded-md leading-relaxed">
        "Water intrusion reported in upper unit ceiling during heavy rain. Requesting roof
        inspection..."
      </div>

      {/* Footer */}
      <div className="flex justify-between text-[0.8rem] text-text-muted border-t border-border-color pt-3">
        <div>Detected: Today, 7:15 AM</div>
        <div className="text-status-blue underline cursor-pointer hover:text-text-primary transition-colors">
          View City Record ↗
        </div>
      </div>
    </div>
  );
};

export default HowItWorksPage;
