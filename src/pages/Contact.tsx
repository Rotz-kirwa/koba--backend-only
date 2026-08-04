import { useState } from "react";
import { motion } from "framer-motion";
import { Mail, Phone, MapPin, Send, Instagram } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const Contact = () => {
  const { toast } = useToast();
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    subject: "",
    message: "",
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    toast({
      title: "Message Sent!",
      description: "We'll get back to you within 24 hours.",
    });
    setFormData({ name: "", email: "", subject: "", message: "" });
  };

  return (
    <div className="min-h-screen pt-24 pb-20">
      <div className="container mx-auto px-4 max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          className="text-center mb-16"
        >
          <p className="text-sm tracking-[0.3em] uppercase text-primary font-body mb-4">Get In Touch</p>
          <h1 className="font-display text-4xl md:text-5xl lg:text-6xl font-light mb-6">
            Contact <span className="italic text-gold-gradient">Queen Koba</span>
          </h1>
          <p className="text-muted-foreground font-body max-w-2xl mx-auto">
            Have questions about our products? We're here to help you on your journey to radiant, healthy skin.
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Contact Information */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2, duration: 0.7 }}
            className="lg:col-span-1 space-y-6"
          >
            <div className="luxury-card">
              <div className="flex items-start gap-4 mb-6">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Mail className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-display text-xl font-semibold mb-2">Email Us</h3>
                  <a
                    href="mailto:info@queenkoba.com"
                    className="text-muted-foreground hover:text-primary transition-colors font-body"
                  >
                    info@queenkoba.com
                  </a>
                </div>
              </div>

              <div className="flex items-start gap-4 mb-6">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Phone className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-display text-xl font-semibold mb-2">Call Us</h3>
                  <a
                    href="tel:+254119559180"
                    className="text-muted-foreground hover:text-primary transition-colors font-body"
                  >
                    0119 559 180
                  </a>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <MapPin className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-display text-xl font-semibold mb-2">Visit Us</h3>
                  <p className="text-muted-foreground font-body">
                    Nairobi, Kenya
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4 mt-6 pt-6 border-t border-border">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Instagram className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h3 className="font-display text-xl font-semibold mb-2">Follow Us</h3>
                  <a
                    href="https://www.instagram.com/queenkoba?igsh=MTJmNXdjazNqMHR3Zw=="
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-muted-foreground hover:text-primary transition-colors font-body"
                  >
                    @queenkoba
                  </a>
                </div>
              </div>
            </div>

            <div className="luxury-card">
              <h3 className="font-display text-xl font-semibold mb-4">Business Hours</h3>
              <div className="space-y-2 text-sm font-body">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Monday - Friday</span>
                  <span>9:00 AM - 6:00 PM</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Saturday</span>
                  <span>10:00 AM - 4:00 PM</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Sunday</span>
                  <span className="text-muted-foreground">Closed</span>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Contact Form */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4, duration: 0.7 }}
            className="lg:col-span-2"
          >
            <form onSubmit={handleSubmit} className="luxury-card">
              <h2 className="font-display text-3xl font-semibold mb-6">Send Us a Message</h2>
              <div className="space-y-6">
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-body mb-2">Your Name *</label>
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 bg-background border border-border rounded-sm focus:outline-none focus:border-primary transition-colors"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-body mb-2">Your Email *</label>
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 bg-background border border-border rounded-sm focus:outline-none focus:border-primary transition-colors"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-body mb-2">Subject *</label>
                  <input
                    type="text"
                    name="subject"
                    value={formData.subject}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 bg-background border border-border rounded-sm focus:outline-none focus:border-primary transition-colors"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-body mb-2">Message *</label>
                  <textarea
                    name="message"
                    value={formData.message}
                    onChange={handleInputChange}
                    rows={6}
                    className="w-full px-4 py-3 bg-background border border-border rounded-sm focus:outline-none focus:border-primary transition-colors resize-none"
                    required
                  />
                </div>

                <button
                  type="submit"
                  className="w-full py-4 bg-gold-gradient text-primary-foreground font-body font-bold text-sm tracking-widest uppercase rounded-sm hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
                >
                  <Send className="w-4 h-4" />
                  Send Message
                </button>
              </div>
            </form>
          </motion.div>
        </div>

        {/* FAQ Section */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.7 }}
          className="mt-16"
        >
          <div className="text-center mb-12">
            <h2 className="font-display text-3xl md:text-4xl font-light mb-4">
              Frequently Asked <span className="italic text-gold-gradient">Questions</span>
            </h2>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="luxury-card">
              <h3 className="font-display text-xl font-semibold mb-3">How long does shipping take?</h3>
              <p className="text-sm text-muted-foreground font-body leading-relaxed">
                We deliver within 2-5 business days in Nairobi and 3-7 business days for other regions in Kenya. Free shipping on orders over KSh 5,000.
              </p>
            </div>

            <div className="luxury-card">
              <h3 className="font-display text-xl font-semibold mb-3">Are your products safe for sensitive skin?</h3>
              <p className="text-sm text-muted-foreground font-body leading-relaxed">
                Yes! Our products are formulated specifically for melanin-rich skin and are free from mercury, hydroquinone, and steroids. We recommend a patch test before first use.
              </p>
            </div>

            <div className="luxury-card">
              <h3 className="font-display text-xl font-semibold mb-3">Can I return a product?</h3>
              <p className="text-sm text-muted-foreground font-body leading-relaxed">
                We offer a 30-day satisfaction guarantee. If you're not happy with your purchase, contact us at info@queenkoba.com for a return or exchange.
              </p>
            </div>

            <div className="luxury-card">
              <h3 className="font-display text-xl font-semibold mb-3">How do I track my order?</h3>
              <p className="text-sm text-muted-foreground font-body leading-relaxed">
                Once your order ships, you'll receive a tracking number via email. You can also contact us for order updates.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Contact;
