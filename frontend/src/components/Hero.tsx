import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import { Link } from "react-router-dom";

const heroImages = [
  { desktop: "/images/hero/desktop/hero-1.jpg", mobile: "/images/hero/mobile/hero-1.jpg" },
  { desktop: "/images/hero/desktop/hero-2.jpg", mobile: "/images/hero/mobile/hero-2.jpg" },
  { desktop: "/images/hero/desktop/hero-3.jpg", mobile: "/images/hero/mobile/hero-3.jpg" },
  { desktop: "/images/hero/desktop/hero-4.jpg", mobile: "/images/hero/mobile/hero-4.jpg" },
  { desktop: "/images/hero/desktop/hero-5.jpg", mobile: "/images/hero/mobile/hero-5.jpg" },
  { desktop: "/images/hero/desktop/hero-6.jpg", mobile: "/images/hero/mobile/hero-6.jpg" },
  { desktop: "/images/hero/desktop/hero-7.jpg", mobile: "/images/hero/mobile/hero-7.jpg" },
  { desktop: "/images/hero/desktop/hero-8.jpg", mobile: "/images/hero/mobile/hero-8.jpg" },
  { desktop: "/images/hero/desktop/hero-9.jpg", mobile: "/images/hero/mobile/hero-9.jpg" },
];

const Hero = () => {
  const [currentImage, setCurrentImage] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentImage((prev) => (prev + 1) % heroImages.length);
    }, 4000);

    return () => clearInterval(interval);
  }, []);
  return (
    <section className="relative h-screen min-h-[600px] max-h-[900px] flex items-center overflow-hidden">
      <div className="absolute inset-0 overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentImage}
            className="absolute inset-0 overflow-hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 1 }}
          >
            <picture className="w-full h-full">
              <source
                media="(min-width: 1024px)"
                srcSet={heroImages[currentImage].desktop}
                type="image/jpeg"
              />
              <source
                media="(max-width: 1023px)"
                srcSet={heroImages[currentImage].mobile}
                type="image/jpeg"
              />
              <img
                src={heroImages[currentImage].desktop}
                alt="Queen Koba - radiant melanin-rich skin"
                className="w-full h-full object-cover"
                style={{ 
                  maxWidth: '100%', 
                  maxHeight: '100%', 
                  objectFit: 'cover', 
                  display: 'block',
                  objectPosition: currentImage === 0 ? 'center' : 'center 40%'
                }}
                loading="lazy"
                decoding="async"
              />
            </picture>
          </motion.div>
        </AnimatePresence>
        <div className="absolute inset-0 hero-overlay" />
      </div>

      <div className="relative container mx-auto px-4 py-32 md:py-0">
        <div className="max-w-2xl">
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.6 }}
            className="text-sm tracking-[0.3em] uppercase text-primary font-body mb-6"
          >
            Premium Kenyan Skincare
          </motion.p>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.8 }}
            className="font-display text-5xl md:text-7xl lg:text-8xl font-light leading-[0.95] mb-6"
          >
            Reveal Your{" "}
            <span className="text-gold-gradient font-semibold italic">Royal</span>{" "}
            Melanin Glow
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7, duration: 0.6 }}
            className="text-base md:text-lg text-muted-foreground leading-relaxed mb-10 max-w-lg font-body"
          >
            Safe. Natural. Powerful. Crafted in Kenya for queens who deserve radiant, even, healthy skin — without toxins.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1, duration: 0.6 }}
            className="hidden sm:flex flex-col sm:flex-row gap-4"
          >
            <Link
              to="/shop"
              className="group relative inline-flex items-center justify-center px-6 py-3 sm:px-8 sm:py-4 overflow-hidden font-body font-bold text-xs sm:text-sm tracking-widest uppercase rounded-sm transition-all duration-300"
            >
              {/* Animated background */}
              <span className="absolute inset-0 bg-gold-gradient" />
              <span className="absolute inset-0 bg-gradient-to-r from-primary via-accent to-primary bg-[length:200%_100%] animate-shimmer opacity-0 group-hover:opacity-100 transition-opacity" />
              
              {/* Glow effect */}
              <span className="absolute inset-0 rounded-sm blur-xl bg-primary/50 opacity-0 group-hover:opacity-100 transition-opacity" />
              
              {/* Button content */}
              <span className="relative flex items-center gap-2 text-primary-foreground">
                <span className="group-hover:translate-x-1 transition-transform">Shop Now</span>
                <svg
                  className="w-5 h-5 group-hover:translate-x-2 transition-transform"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2.5}
                    d="M13 7l5 5m0 0l-5 5m5-5H6"
                  />
                </svg>
              </span>
              
              {/* Shine effect */}
              <span className="absolute inset-0 rounded-sm overflow-hidden">
                <span className="absolute inset-0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/30 to-transparent" />
              </span>
            </Link>
          </motion.div>

          {/* Mobile floating button */}
          <Link
            to="/shop"
            className="sm:hidden fixed bottom-8 left-8 z-50 group inline-flex items-center justify-center px-5 py-3 overflow-hidden font-body font-bold text-xs tracking-widest uppercase rounded-full shadow-2xl transition-all duration-300"
          >
            {/* Animated background */}
            <span className="absolute inset-0 bg-gold-gradient" />
            <span className="absolute inset-0 bg-gradient-to-r from-primary via-accent to-primary bg-[length:200%_100%] animate-shimmer opacity-0 group-hover:opacity-100 transition-opacity" />
            
            {/* Button content */}
            <span className="relative flex items-center gap-2 text-primary-foreground">
              <span>Shop Now</span>
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2.5}
                  d="M13 7l5 5m0 0l-5 5m5-5H6"
                />
              </svg>
            </span>
          </Link>
        </div>
      </div>
    </section>
  );
};

export default Hero;
