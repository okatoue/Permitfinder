import React from 'react';
import { Link } from 'react-router-dom';
import Button from '../components/Button';
import Footer from '../components/Footer';
import CoverageMap from '../components/CoverageMap';

/**
 * PricingPage component - converted from pricing.html
 * Displays pricing plans, coverage map, and FAQ
 */
const PricingPage = () => {
  const faqs = [
    {
      question: 'Are leads exclusive?',
      answer: 'Semi-exclusive. We cap every ZIP at exactly 2 subscribers to prevent overcrowding.',
    },
    {
      question: 'Can I change ZIPs?',
      answer: 'Yes, 1 swap/month is included.',
    },
    {
      question: 'When are emails sent?',
      answer: 'Daily subscribers: Every morning (M-F). Weekly subscribers: Monday mornings.',
    },
    {
      question: 'Do you include phone numbers?',
      answer: "No. We provide the address, owner name, and permit details. We focus on verifiable city data, not scraping private numbers.",
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Pricing Header */}
      <header className="max-w-[600px] mx-auto text-center py-16">
        <h1 className="text-4xl md:text-[2.5rem] font-bold text-text-primary mb-4">
          Simple monthly plans.
        </h1>
        <p className="text-lg text-text-secondary">
          Choose how often you want leads. Cancel anytime.
        </p>
      </header>

      {/* Pricing Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16 items-start">
        {/* Weekly Plan */}
        <PlanCard
          name="Weekly Leads"
          price="$299"
          description="For steady pipeline + smaller teams."
          features={[
            'Up to 10 Seattle ZIP codes',
            { text: 'Email every ', highlight: 'Monday morning' },
            'Full Dashboard access',
            '2 seats per ZIP (shared cap)',
            '1 ZIP swap per month',
          ]}
          buttonText="Start Weekly"
          buttonVariant="secondary"
        />

        {/* Daily Plan - Featured */}
        <PlanCard
          name="Daily Leads"
          price="$599"
          description="For aggressive growth + faster response."
          features={[
            'Up to 20 Seattle ZIP codes',
            { text: 'Email ', highlight: 'Every Morning (M-F)' },
            'Full Dashboard access',
            '2 seats per ZIP (shared cap)',
            '1 ZIP swap per month',
          ]}
          buttonText="Start Daily"
          buttonVariant="primary"
          featured
          badge="Most Popular"
        />
      </div>

      {/* Add-ons Section */}
      <div className="bg-[rgba(22,28,38,0.5)] border border-border-color rounded-lg p-6 mb-20 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div className="font-semibold text-lg">
          <span className="block text-[0.8rem] text-text-muted uppercase tracking-wider mb-1">
            Scale Up
          </span>
          Need more ZIP codes?
        </div>
        <div className="flex flex-col md:flex-row gap-6 md:gap-10">
          <div>
            <div className="text-[0.85rem] text-text-muted">Weekly Plan</div>
            <div className="text-text-primary font-bold">
              +$20 <span className="font-normal text-[0.85rem] text-text-muted">/ ZIP</span>
            </div>
          </div>
          <div>
            <div className="text-[0.85rem] text-text-muted">Daily Plan</div>
            <div className="text-accent font-bold">
              +$25 <span className="font-normal text-[0.85rem] text-text-muted">/ ZIP</span>
            </div>
          </div>
        </div>
      </div>

      {/* Coverage Section */}
      <section className="bg-bg-card border border-border-color rounded-xl p-10 md:p-16 mb-24 relative overflow-hidden">
        {/* Grid Background */}
        <div
          className="absolute inset-0 opacity-20 pointer-events-none"
          style={{
            backgroundImage: 'radial-gradient(var(--border) 1px, transparent 1px)',
            backgroundSize: '30px 30px',
          }}
        />

        <div className="relative z-10">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-text-primary mb-2">Seattle Coverage</h2>
            <p className="text-text-secondary max-w-[500px] mx-auto">
              ZIP-based territories with strictly limited seats.
            </p>
          </div>

          {/* Coverage Map Component */}
          <div className="mb-10">
            <CoverageMap />
          </div>

          <div className="text-center">
            <Button variant="primary" href="#" className="inline-block w-auto min-w-[250px]">
              Check Availability in Signup
            </Button>
          </div>

          {/* Coverage Rules */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-10 mt-10 pt-10 border-t border-border-color">
            <div>
              <h4 className="text-text-primary font-semibold mb-2">Strict 2-Subscriber Cap</h4>
              <p className="text-text-secondary text-[0.95rem]">
                We do not resell data to the highest bidder. Once 2 roofers subscribe to a ZIP, it is locked. You can join a waitlist or pick a different zone.
              </p>
            </div>
            <div>
              <h4 className="text-text-primary font-semibold mb-2">Flexible Territory</h4>
              <p className="text-text-secondary text-[0.95rem]">
                Market shifting? You get <strong>1 ZIP swap per month</strong> included in your plan so you can adjust your strategy.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="max-w-[800px] mx-auto mb-24">
        <h2 className="text-3xl font-bold text-text-primary text-center mb-8">Common Questions</h2>
        <div>
          {faqs.map((faq, index) => (
            <FAQItem key={index} question={faq.question} answer={faq.answer} />
          ))}
        </div>
        <p className="text-center text-text-secondary mt-8">
          Have more questions? Check out the{' '}
          <Link to="/contact#faq" className="text-accent hover:underline">
            FAQ
          </Link>{' '}
          or{' '}
          <Link to="/contact" className="text-accent hover:underline">
            contact us
          </Link>
          .
        </p>
      </section>

      <Footer />
    </div>
  );
};

/**
 * Plan Card component
 */
const PlanCard = ({
  name,
  price,
  description,
  features,
  buttonText,
  buttonVariant = 'secondary',
  featured = false,
  badge,
}) => {
  return (
    <div
      className={`relative rounded-xl p-8 md:p-10 transition-transform
        ${featured
          ? 'border border-accent bg-gradient-to-b from-[#131A24] to-bg-card shadow-[0_20px_40px_rgba(0,0,0,0.4)] scale-[1.02]'
          : 'bg-bg-card border border-border-color'
        }`}
    >
      {badge && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-accent text-accent-text text-[0.75rem] font-extrabold px-3 py-1 rounded-full uppercase tracking-wider">
          {badge}
        </div>
      )}

      <div className={`text-xl font-semibold mb-2 ${featured ? 'text-accent' : 'text-text-primary'}`}>
        {name}
      </div>
      <div className="text-[2.5rem] font-extrabold text-text-primary mb-1">
        {price}
        <span className="text-base text-text-muted font-normal">/mo</span>
      </div>
      <p className="text-text-muted text-[0.95rem] mb-8 pb-5 border-b border-border-color">
        {description}
      </p>

      <ul className="space-y-3 mb-8">
        {features.map((feature, index) => (
          <li key={index} className="flex items-center gap-3 text-[0.95rem] text-text-secondary">
            <span className="text-accent">✓</span>
            {typeof feature === 'string' ? (
              feature
            ) : (
              <>
                {feature.text}
                <strong>{feature.highlight}</strong>
              </>
            )}
          </li>
        ))}
      </ul>

      <Button variant={buttonVariant} href="#" className="w-full">
        {buttonText}
      </Button>
    </div>
  );
};

/**
 * FAQ Item component
 */
const FAQItem = ({ question, answer }) => {
  return (
    <div className="border-b border-border-color py-6">
      <div className="font-semibold text-lg text-text-primary mb-2">{question}</div>
      <div className="text-text-secondary text-[0.95rem]">{answer}</div>
    </div>
  );
};

export default PricingPage;
