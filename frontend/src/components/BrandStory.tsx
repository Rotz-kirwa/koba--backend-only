import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import { ShieldCheck, Leaf, FlaskConical } from "lucide-react";

const BrandStory = () => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-100px" });

  const issues = [
    { title: "Hyperpigmentation", desc: "Excess melanin production causing dark patches and uneven complexion." },
    { title: "Uneven Tone", desc: "Sun damage and inflammation creating inconsistent skin coloring." },
    { title: "Dark Spots", desc: "Post-inflammatory marks that linger after breakouts or irritation." },
    { title: "Toxic Creams", desc: "Mercury & hydroquinone products causing irreversible skin and organ damage." },
  ];

  return (
    <section id="story" className="section-spacing bg-secondary/30">
      <div className="container mx-auto px-4" ref={ref}>
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8 }}
          className="text-center max-w-3xl mx-auto mb-16"
        >
          <p className="text-sm tracking-[0.3em] uppercase text-primary font-body mb-4">The Problem</p>
          <h2 className="font-display text-4xl md:text-5xl lg:text-6xl font-light mb-6">
            Your Melanin Deserves <span className="italic text-gold-gradient">Better</span>
          </h2>
          <p className="text-muted-foreground font-body leading-relaxed">
            Millions of women risk their health with dangerous bleaching creams. Queen Koba is the safe complexion-clarifying revolution — inspired by African queens, crafted proudly in Kenya.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {issues.map((issue, i) => (
            <motion.div
              key={issue.title}
              initial={{ opacity: 0, y: 30 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.2 + i * 0.1, duration: 0.6 }}
              className="luxury-card text-center"
            >
              <h3 className="font-display text-xl font-semibold text-primary mb-3">{issue.title}</h3>
              <p className="text-sm text-muted-foreground font-body">{issue.desc}</p>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ delay: 0.6, duration: 0.8 }}
          className="flex flex-wrap justify-center gap-8 md:gap-16"
        >
          {[
            { icon: ShieldCheck, label: "Safe & Certified" },
            { icon: Leaf, label: "African Botanicals" },
            { icon: FlaskConical, label: "Science-Backed" },
          ].map(({ icon: Icon, label }) => (
            <div key={label} className="flex items-center gap-3 text-foreground">
              <Icon className="w-6 h-6 text-primary" />
              <span className="font-body text-sm tracking-wide uppercase">{label}</span>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
};

export default BrandStory;
