import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Link } from "react-router-dom";

const FinalCTA = () => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section className="section-spacing bg-secondary/30">
      <div className="container mx-auto px-4 text-center" ref={ref}>
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8 }}
          className="max-w-2xl mx-auto"
        >
          <p className="text-sm tracking-[0.3em] uppercase text-primary font-body mb-6">Your Throne Awaits</p>
          <h2 className="font-display text-5xl md:text-6xl lg:text-7xl font-light mb-6">
            Claim Your <span className="italic text-gold-gradient">Glow</span> Today
          </h2>
          <p className="text-muted-foreground font-body mb-4">
            Free Shipping over KSh 5,000 · Limited Launch Stock
          </p>
          <div className="line-gold max-w-xs mx-auto mb-10" />
          <Link
            to="/shop"
            className="inline-flex items-center justify-center px-10 py-4 bg-gold-gradient text-primary-foreground font-body font-bold text-sm tracking-widest uppercase rounded-sm hover:opacity-90 transition-opacity"
          >
            Shop Queen Koba →
          </Link>
        </motion.div>
      </div>
    </section>
  );
};

export default FinalCTA;
