import { motion, useInView } from "framer-motion";
import { useRef, useState } from "react";
import { Star, Plus, Minus, ShoppingBag } from "lucide-react";
import { products } from "@/data/products";
import { useCart } from "@/context/CartContext";

const ProductCard = ({ product, index }: { product: typeof products[0]; index: number }) => {
  const [qty, setQty] = useState(1);
  const { addToCart } = useCart();
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-50px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ delay: index * 0.1, duration: 0.6 }}
      className={`luxury-card flex flex-col overflow-hidden p-0 ${product.isBundle ? "border-primary/40" : ""}`}
    >
      {product.image && (
        <div className="w-full overflow-hidden">
          <img
            src={product.image}
            alt={product.name}
            className="w-full h-56 object-cover"
            loading="lazy"
          />
        </div>
      )}

      <div className="p-8 flex flex-col flex-1">
        {product.isBundle && (
          <div className="bg-gold-gradient text-primary-foreground text-xs font-body font-bold tracking-widest uppercase px-4 py-2 rounded-sm self-start mb-4 -mt-2">
            15% OFF - Best Value
          </div>
        )}

        <h3 className="font-display text-xl md:text-2xl font-semibold mb-2">{product.name}</h3>
        <p className="text-sm text-muted-foreground font-body mb-4 leading-relaxed">{product.description}</p>

        <div className="flex items-center gap-2 mb-4">
          <div className="flex">
            {Array.from({ length: 5 }).map((_, i) => (
              <Star
                key={i}
                className={`w-4 h-4 ${i < Math.floor(product.rating) ? "text-primary fill-primary" : "text-muted-foreground/30"}`}
              />
            ))}
          </div>
          <span className="text-xs text-muted-foreground font-body">
            {product.rating}/5 ({product.reviews} reviews)
          </span>
        </div>

        <div className="flex items-end justify-between gap-4 mt-auto pt-4 border-t border-border/50">
          <div>
            <span className="font-display text-2xl font-semibold text-primary">
              KSh {product.price.toLocaleString()}
            </span>
            {product.originalPrice && (
              <span className="ml-2 text-sm text-muted-foreground line-through font-body">
                KSh {product.originalPrice.toLocaleString()}
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center border border-border rounded-sm">
              <button
                onClick={() => setQty(Math.max(1, qty - 1))}
                className="p-2 text-muted-foreground hover:text-foreground transition-colors"
                aria-label="Decrease quantity"
              >
                <Minus className="w-3 h-3" />
              </button>
              <span className="px-3 text-sm font-body">{qty}</span>
              <button
                onClick={() => setQty(qty + 1)}
                className="p-2 text-muted-foreground hover:text-foreground transition-colors"
                aria-label="Increase quantity"
              >
                <Plus className="w-3 h-3" />
              </button>
            </div>

            <button
              onClick={() => {
                addToCart(product, qty);
                setQty(1);
              }}
              className="flex items-center gap-2 px-5 py-2.5 bg-gold-gradient text-primary-foreground font-body text-xs font-bold tracking-widest uppercase rounded-sm hover:opacity-90 transition-opacity"
            >
              <ShoppingBag className="w-4 h-4" />
              {product.isBundle ? "Get the Bundle" : "Add to Cart"}
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

const ProductStore = () => {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <section id="shop" className="section-spacing bg-gradient-to-b from-background to-secondary/20">
      <div className="container mx-auto px-4 max-w-6xl" ref={ref}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7 }}
          className="text-center mb-12"
        >
          <p className="text-sm tracking-[0.3em] uppercase text-primary font-body mb-4">Your Royal Routine</p>
          <h2 className="font-display text-4xl md:text-5xl lg:text-6xl font-light mb-4">
            Build Your Glow - <span className="italic text-gold-gradient">Step by Step</span>
          </h2>
          <p className="text-muted-foreground font-body max-w-3xl mx-auto">
            Complexion-Clarifying essentials tailored for melanin-rich skin. Select your routine or save with the full bundle.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {products.map((product, i) => (
            <ProductCard key={product.id} product={product} index={i} />
          ))}
        </div>

        <div className="luxury-card mt-10 text-center">
          <h3 className="font-display text-3xl mb-2">Bundle & Save: Full Royal Routine - KSh 8,000 (15% Off!)</h3>
          <p className="text-primary font-bold tracking-wide uppercase text-sm">Get the Bundle →</p>
        </div>
      </div>
    </section>
  );
};

export default ProductStore;
