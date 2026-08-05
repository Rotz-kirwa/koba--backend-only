import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Star } from "lucide-react";

const testimonials = [
  { 
    quote: "Finally, even glowing skin without fear! My dark spots are fading naturally.", 
    handle: "@melaninqueenke",
    image: "https://i.pinimg.com/1200x/52/3e/4a/523e4ad977fc8ef4b730927561d297b6.jpg"
  },
  { 
    quote: "Queen Koba transformed my routine—hydrated, radiant, and proudly Kenyan-made!", 
    handle: "@nairobiglow",
    image: "https://i.pinimg.com/736x/50/08/96/50089636b6995de2446ec29d28346a7e.jpg"
  },
  { 
    quote: "Safe, effective, and empowering. My complexion is clearer than ever.", 
    handle: "@africanroyalty",
    image: "https://i.pinimg.com/1200x/02/58/95/025895de41978e8191e69cd862180bcb.jpg"
  },
  { 
    quote: "My skin has never felt this nourished! Queen Koba is a game-changer for melanin-rich skin.", 
    handle: "@glowingqueen254",
    image: "https://i.pinimg.com/736x/64/7a/73/647a737eaa080930fbbbdaccaf2df30e.jpg"
  },
  { 
    quote: "I love how gentle yet effective these products are. My confidence has skyrocketed!", 
    handle: "@beautybykamau",
    image: "https://i.pinimg.com/736x/e3/dd/6c/e3dd6c33df67489cfb973134289f6f68.jpg"
  },
  { 
    quote: "Queen Koba gave me the even tone I've always wanted. No harsh chemicals, just results!", 
    handle: "@radiantafrica",
    image: "https://i.pinimg.com/1200x/98/08/46/98084619be815a8c319a98f1c0bc8e25.jpg"
  },
  { 
    quote: "Best skincare investment I've made! My skin glows naturally and feels amazing.", 
    handle: "@queenlyvibes",
    image: "https://i.pinimg.com/736x/c4/7a/ba/c47aba3e1e8fb99bcf314c07aca1063b.jpg"
  },
  { 
    quote: "Queen Koba restored my skin's natural radiance. I feel beautiful in my own skin!", 
    handle: "@melaninmagic",
    image: "https://i.pinimg.com/1200x/d8/12/4f/d8124f24adb47f1b392b612a3d1c2e5d.jpg"
  },
];

const Testimonials = () => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section id="reviews" className="section-spacing">
      <div className="container mx-auto px-4" ref={ref}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7 }}
          className="text-center mb-16"
        >
          <p className="text-sm tracking-[0.3em] uppercase text-primary font-body mb-4">Royal Reviews</p>
          <h2 className="font-display text-4xl md:text-5xl lg:text-6xl font-light mb-4">
            Loved by <span className="italic text-gold-gradient">Queens</span>
          </h2>
          <div className="flex items-center justify-center gap-2 mt-4">
            <div className="flex">
              {Array.from({ length: 5 }).map((_, i) => (
                <Star key={i} className="w-5 h-5 text-primary fill-primary" />
              ))}
            </div>
            <span className="font-body text-sm text-muted-foreground">4.8/5 from 1M+ Queens Worldwide</span>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
          {testimonials.map((t, i) => (
            <motion.div
              key={t.handle}
              initial={{ opacity: 0, y: 30 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.2 + i * 0.15, duration: 0.6 }}
              className="luxury-card overflow-hidden p-0 text-center"
            >
              <div className="w-full h-64 overflow-hidden">
                <img 
                  src={t.image} 
                  alt={t.handle}
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="p-8">
                <div className="flex justify-center mb-4">
                  {Array.from({ length: 5 }).map((_, j) => (
                    <Star key={j} className="w-4 h-4 text-primary fill-primary" />
                  ))}
                </div>
                <p className="font-display text-xl italic mb-4 leading-relaxed">"{t.quote}"</p>
                <p className="font-body text-sm text-primary tracking-wide">{t.handle}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Testimonials;
