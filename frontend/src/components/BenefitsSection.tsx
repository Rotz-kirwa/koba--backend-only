import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Sparkles, Droplets, Leaf } from "lucide-react";

const benefits = [
  {
    icon: Sparkles,
    title: "Evens Tone & Fades Dark Spots",
    desc: "Clinically-inspired actives target hyperpigmentation at the source, revealing a luminous, even complexion.",
  },
  {
    icon: Droplets,
    title: "Deep Hydration & Barrier Support",
    desc: "Ceramides, Hyaluronic Acid, and Moringa Oil lock in moisture and strengthen your natural skin barrier.",
  },
  {
    icon: Leaf,
    title: "Powered by African Botanicals",
    desc: "Qasil, Moringa, and Liwa — time-honored East African beauty secrets meet modern dermal science.",
  },
];

const BenefitsSection = () => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section className="section-spacing">
      <div className="container mx-auto px-4" ref={ref}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7 }}
          className="text-center mb-16"
        >
          <p className="text-sm tracking-[0.3em] uppercase text-primary font-body mb-4">Why Queen Koba</p>
          <h2 className="font-display text-4xl md:text-5xl lg:text-6xl font-light">
            The Royal <span className="italic text-gold-gradient">Difference</span>
          </h2>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {benefits.map((b, i) => (
            <motion.div
              key={b.title}
              initial={{ opacity: 0, y: 40 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.2 + i * 0.15, duration: 0.7 }}
              className="luxury-card text-center group"
            >
              <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors duration-500">
                <b.icon className="w-7 h-7 text-primary" />
              </div>
              <h3 className="font-display text-2xl font-semibold mb-4">{b.title}</h3>
              <p className="text-muted-foreground font-body text-sm leading-relaxed">{b.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default BenefitsSection;
