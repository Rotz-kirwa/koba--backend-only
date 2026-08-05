import { motion, useInView } from "framer-motion";
import { useRef, useState } from "react";
import { ShieldCheck, ShieldOff, FlaskConical, MapPin } from "lucide-react";

const keyIngredients = [
  { name: "Purifying Qasil", desc: "Ancient Somali beauty leaf that deeply cleanses, brightens, and tightens pores naturally." },
  { name: "Antioxidant Moringa", desc: "East African superfood oil rich in oleic acid — fights free radicals and deeply nourishes." },
  { name: "Tranexamic Acid", desc: "Gold-standard brightening active that inhibits melanin transfer for visible clarity." },
  { name: "Niacinamide", desc: "Vitamin B3 powerhouse — minimizes pores, strengthens barrier, and evens skin tone." },
  { name: "Kojic Dipalmitate", desc: "Gentle, stable tyrosinase inhibitor that fades dark spots without irritation." },
];

const trustBadges = [
  { icon: ShieldOff, label: "No Mercury" },
  { icon: ShieldOff, label: "No Hydroquinone" },
  { icon: ShieldCheck, label: "No Steroids" },
  { icon: MapPin, label: "Crafted in Kenya" },
];

const inciList = [
  "Aloe Barbadensis Leaf Juice", "Cetearyl Olivate", "Snail Secretion Filtrate",
  "Niacinamide", "Tranexamic Acid", "Azelaic Acid", "Kojic Dipalmitate",
  "Glycyrrhiza Glabra Root Extract", "Centella Asiatica Extract",
  "Moringa Oleifera Seed Oil", "Hyaluronic Acid", "Ceramide NP/AP/EOP",
  "Allantoin", "Tocopherol", "Qasil", "Liwa", "Disodium EDTA",
  "Xanthan Gum", "Geogard ECT", "Jasmine-Citrus Essential Oil Blend",
];

const IngredientsSpotlight = () => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-100px" });
  const [showInci, setShowInci] = useState(false);

  return (
    <section id="ingredients" className="section-spacing bg-secondary/30">
      <div className="container mx-auto px-4" ref={ref}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7 }}
          className="text-center mb-16"
        >
          <p className="text-sm tracking-[0.3em] uppercase text-primary font-body mb-4">Full Ingredient Transparency</p>
          <h2 className="font-display text-4xl md:text-5xl lg:text-6xl font-light">
            Because Queens Deserve to <span className="italic text-gold-gradient">Know</span>
          </h2>
          <p className="text-muted-foreground font-body mt-4 max-w-3xl mx-auto">
            We believe in complete honesty. Below is the full INCI ingredient list for our core formulas. Ingredients listed in descending order of predominance. No mercury, no hydroquinone, no steroids. Crafted with care in Kenya.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
          {keyIngredients.map((ing, i) => (
            <motion.div
              key={ing.name}
              initial={{ opacity: 0, y: 30 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.1 + i * 0.1, duration: 0.6 }}
              className="luxury-card"
            >
              <div className="flex items-center gap-3 mb-3">
                <FlaskConical className="w-5 h-5 text-primary" />
                <h3 className="font-display text-xl font-semibold">{ing.name}</h3>
              </div>
              <p className="text-sm text-muted-foreground font-body leading-relaxed">{ing.desc}</p>
            </motion.div>
          ))}
        </div>

        {/* Trust Badges */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={inView ? { opacity: 1 } : {}}
          transition={{ delay: 0.6, duration: 0.6 }}
          className="grid grid-cols-2 md:flex md:flex-wrap justify-center gap-4 md:gap-6 lg:gap-10 mb-16"
        >
          {trustBadges.map(({ icon: Icon, label }) => (
            <div key={label} className="flex items-center gap-2 px-4 py-3 border border-primary/20 rounded-sm justify-center">
              <Icon className="w-5 h-5 text-primary" />
              <span className="font-body text-xs tracking-widest uppercase">{label}</span>
            </div>
          ))}
        </motion.div>

        {/* INCI Transparency */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={inView ? { opacity: 1 } : {}}
          transition={{ delay: 0.8, duration: 0.6 }}
          className="max-w-3xl mx-auto text-center"
        >
          <button
            onClick={() => setShowInci(!showInci)}
            className="font-body text-sm tracking-widest uppercase text-primary hover:text-primary/80 transition-colors border-b border-primary/30 pb-1"
          >
            {showInci ? "Hide" : "View"} Full INCI List
          </button>

          {showInci && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="mt-8 luxury-card text-left"
            >
              <h4 className="font-display text-lg font-semibold text-primary mb-4">Full Ingredient Transparency – Because Queens Deserve to Know</h4>
              <p className="font-body text-sm text-muted-foreground leading-loose mb-4">
                We believe in complete honesty. Below is the full INCI ingredient list for our core formulas (shared base across the line, with minor variations per product—check individual product pages for exacts). Ingredients listed in descending order of predominance. No mercury, no hydroquinone, no steroids. Crafted with care in Kenya.
              </p>
              <p className="font-body text-sm text-muted-foreground leading-loose">
                {inciList.join(" · ")}
              </p>
            </motion.div>
          )}
        </motion.div>
      </div>
    </section>
  );
};

export default IngredientsSpotlight;
