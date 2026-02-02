import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import Button from '../components/Button';
import Footer from '../components/Footer';

/**
 * ContactPage component - converted from contact.html
 * Contact form, demo booking, and FAQ
 */
const ContactPage = () => {
  const [formData, setFormData] = useState({
    name: '',
    company: '',
    email: '',
    phone: '',
    zips: '',
    bestTime: '',
    message: '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Form submission logic would go here
    console.log('Form submitted:', formData);
  };

  const faqsLeft = [
    {
      question: 'What exactly am I getting?',
      answer:
        'A dashboard + an email digest of fresh roofing-related opportunities in your selected Seattle ZIP codes, complete with CSV export for your CRM.',
    },
    {
      question: 'Are leads exclusive?',
      answer:
        "Leads are shared, but we limit territories to 2 seats per ZIP so you're not competing with a crowd.",
    },
    {
      question: 'What is a ZIP seat?',
      answer:
        'Each ZIP code has a limited number of subscriber spots ("seats"). When seats are full, that ZIP is marked as sold out.',
    },
    {
      question: 'When do emails go out?',
      answer:
        'Daily plans get a morning email every day (M-F). Weekly plans get a consolidated Monday morning email.',
    },
    {
      question: 'Can I change my ZIP codes?',
      answer: 'Yes—1 ZIP swap per month is included in your subscription.',
    },
  ];

  const faqsRight = [
    {
      question: "What's a lead and why do some show up again?",
      answer:
        'A lead is a unique address. We show new + updated leads so you see important changes (like status updates), not just brand-new records.',
    },
    {
      question: 'Do you provide phone numbers or owner emails?',
      answer:
        'Not in v1. We provide address-based leads with source links and notes. We provide the data you need to run your own outreach strategy.',
    },
    {
      question: 'Where does the data come from?',
      answer:
        'We aggregate data directly from public Seattle city data sources. We provide source links for verification whenever available.',
    },
    {
      question: 'Can I cancel anytime?',
      answer:
        'Yes—cancel any time in your billing portal. Your plan stays active until the end of the current billing period.',
    },
    {
      question: 'Do you cover nearby cities?',
      answer:
        'Not at launch. We are starting Seattle-only for our first customers, then adding nearby city ZIPs (Bellevue, etc.) as an add-on pack later.',
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Page Header */}
      <header className="max-w-[600px] mx-auto text-center py-16">
        <h1 className="text-4xl md:text-[2.5rem] font-bold text-text-primary mb-4">
          Questions? Want a quick demo?
        </h1>
        <p className="text-lg text-text-secondary">
          Tell us your service ZIPs and we'll help you get set up.
        </p>
      </header>

      {/* Contact Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-[3fr_2fr] gap-10 lg:gap-16 mb-24 items-start">
        {/* Left: Contact Form */}
        <div className="bg-bg-card border border-border-color rounded-xl p-8 md:p-10">
          <form onSubmit={handleSubmit}>
            {/* Name & Company Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <FormGroup label="Name">
                <FormInput
                  type="text"
                  name="name"
                  placeholder="Your Name"
                  value={formData.name}
                  onChange={handleChange}
                />
              </FormGroup>
              <FormGroup label="Company">
                <FormInput
                  type="text"
                  name="company"
                  placeholder="Roofing Co."
                  value={formData.company}
                  onChange={handleChange}
                />
              </FormGroup>
            </div>

            <FormGroup label="Email Address">
              <FormInput
                type="email"
                name="email"
                placeholder="you@company.com"
                value={formData.email}
                onChange={handleChange}
              />
            </FormGroup>

            <FormGroup
              label="Phone Number"
              labelSuffix={<span className="text-text-muted font-normal">(Optional)</span>}
            >
              <FormInput
                type="tel"
                name="phone"
                placeholder="(206) 555-0123"
                value={formData.phone}
                onChange={handleChange}
              />
            </FormGroup>

            <FormGroup
              label="ZIPs Served"
              hint="Tell us which Seattle ZIPs you are interested in."
            >
              <FormInput
                type="text"
                name="zips"
                placeholder="e.g. 98103, 98107..."
                value={formData.zips}
                onChange={handleChange}
              />
            </FormGroup>

            <FormGroup label="Best time to reach you">
              <FormInput
                type="text"
                name="bestTime"
                placeholder="e.g. Weekday mornings, PST"
                value={formData.bestTime}
                onChange={handleChange}
              />
            </FormGroup>

            <FormGroup
              label="Message / Plan Preference"
              hint="Do you prefer Daily or Weekly leads?"
            >
              <textarea
                name="message"
                rows={3}
                className="w-full bg-[#0F131A] border border-border-color text-text-primary p-3 rounded-md text-base transition-all duration-200 focus:outline-none focus:border-accent focus:shadow-[0_0_0_1px_var(--accent)] resize-none"
                value={formData.message}
                onChange={handleChange}
              />
            </FormGroup>

            <Button variant="primary" type="submit" className="w-full">
              Send Message
            </Button>

            <p className="text-center mt-4 text-[0.9rem] text-text-muted">
              We'll reply as soon as possible.
            </p>
          </form>
        </div>

        {/* Right: Demo Card & Email */}
        <div>
          {/* Demo Card */}
          <div className="bg-gradient-to-br from-bg-card to-[#1A222E] border border-border-color rounded-xl p-8 text-center mb-6">
            <div className="w-12 h-12 bg-[rgba(46,234,122,0.1)] text-accent rounded-full flex items-center justify-center mx-auto mb-5">
              <CalendarIcon />
            </div>
            <h3 className="text-text-primary font-semibold text-lg mb-2">Book a 15-min Demo</h3>
            <p className="text-text-secondary text-[0.95rem] mb-5">
              Skip the email tag. Pick a time on our calendar to see the dashboard live.
            </p>
            <Button variant="secondary" href="#" className="w-full">
              View Calendar Availability
            </Button>
          </div>

          {/* Direct Email */}
          <div className="text-center">
            <p className="text-text-muted text-[0.9rem] mb-1">Prefer direct email?</p>
            <a
              href="mailto:hello@scopesignals.com"
              className="text-accent font-semibold hover:underline"
            >
              hello@scopesignals.com
            </a>
          </div>
        </div>
      </div>

      {/* FAQ Section */}
      <section id="faq" className="border-t border-border-color pt-20 mb-24">
        <h2 className="text-3xl font-bold text-text-primary text-center mb-10">
          Frequently Asked Questions
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          <div className="space-y-8">
            {faqsLeft.map((faq, index) => (
              <FAQItem key={index} question={faq.question} answer={faq.answer} />
            ))}
          </div>
          <div className="space-y-8">
            {faqsRight.map((faq, index) => (
              <FAQItem key={index} question={faq.question} answer={faq.answer} />
            ))}
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

/**
 * Form Group wrapper component
 */
const FormGroup = ({ label, labelSuffix, hint, children }) => (
  <div className="mb-5">
    <label className="block mb-2 font-semibold text-[0.9rem] text-text-primary">
      {label} {labelSuffix}
    </label>
    {hint && <span className="block text-[0.8rem] text-text-muted mb-2">{hint}</span>}
    {children}
  </div>
);

/**
 * Form Input component
 */
const FormInput = ({ type = 'text', name, placeholder, value, onChange }) => (
  <input
    type={type}
    name={name}
    placeholder={placeholder}
    value={value}
    onChange={onChange}
    className="w-full bg-[#0F131A] border border-border-color text-text-primary p-3 rounded-md text-base transition-all duration-200 focus:outline-none focus:border-accent focus:shadow-[0_0_0_1px_var(--accent)] placeholder:text-text-muted"
  />
);

/**
 * FAQ Item component
 */
const FAQItem = ({ question, answer }) => (
  <div>
    <div className="font-bold text-lg text-text-primary mb-2 flex gap-2">
      <span className="text-accent">Q.</span>
      {question}
    </div>
    <div className="text-text-secondary text-[0.95rem] leading-relaxed pl-7">{answer}</div>
  </div>
);

/**
 * Calendar Icon component
 */
const CalendarIcon = () => (
  <svg
    width="24"
    height="24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    viewBox="0 0 24 24"
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
    />
  </svg>
);

export default ContactPage;
