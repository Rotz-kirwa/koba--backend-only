import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { AlertTriangle } from "lucide-react";

const SafetyDisclaimer = () => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section className="py-16">
      <div className="container mx-auto px-4" ref={ref}>
        <motion.div
          initial={{ opacity: 0 }}
          animate={inView ? { opacity: 1 } : {}}
          transition={{ duration: 0.6 }}
          className="max-w-3xl mx-auto luxury-card border-muted/50"
        >
          <div className="flex items-start gap-4">
            <AlertTriangle className="w-5 h-5 text-primary mt-1 flex-shrink-0" />
            <div>
              <h4 className="font-display text-lg font-semibold mb-3">Important Safety Disclaimer</h4>
              <ul className="space-y-2 text-sm text-muted-foreground font-body leading-relaxed">
                <li>• Patch test recommended on inner arm for 24–48 hours before full use—especially important for melanin-rich skin prone to sensitivity or PIH.</li>
                <li>• Discontinue if irritation occurs. Results vary by individual; not guaranteed to lighten skin tone permanently.</li>
                <li>• For personalized advice, consult a dermatologist.</li>
                <li>• For external use only. Keep out of reach of children.</li>
                <li>• Store in a cool, dry place.</li>
              </ul>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default SafetyDisclaimer;
