import { motion, useInView } from "framer-motion";
import { useRef, useState, useEffect } from "react";
import { Star, Plus, Minus, ShoppingBag } from "lucide-react";
import { useCart } from "@/context/CartContext";
import productsImg from "@/assets/products-bg.jpg";

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

interface Product {
  _id: string;
  name: string;
  description: string;
  category: string;
  prices: {
    KES: { amount: number; symbol: string; country: string };
  };
  in_stock: boolean;
  image_url?: string;
  rating?: number;
  reviews?: number;
}

const ProductCard = ({ product, index }: { product: Product; index: number }) => {
  const [qty, setQty] = useState(1);
  const { addToCart } = useCart();
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-50px" });

  const price = product.prices?.KES?.amount || 0;
  const rating = product.rating || 4.5;
  const reviews = product.reviews || 0;

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ delay: index * 0.1, duration: 0.6 }}
      className="luxury-card flex flex-col overflow-hidden p-0"
    >
      {product.image_url && (
        <div className="w-full overflow-hidden">
          <img 
            src={product.image_url} 
            alt={product.name}
            className="w-full h-56 object-cover"
            loading="lazy"
          />
        </div>
      )}

      <div className="p-8 flex flex-col flex-1">
        <h3 className="font-display text-xl md:text-2xl font-semibold mb-2">{product.name}</h3>
        <p className="text-sm text-muted-foreground font-body mb-4 leading-relaxed">{product.description}</p>

        <div className="flex items-center gap-2 mb-4">
          <div className="flex">
            {Array.from({ length: 5 }).map((_, i) => (
              <Star
                key={i}
                className={`w-4 h-4 ${i < Math.floor(rating) ? "text-primary fill-primary" : "text-muted-foreground/30"}`}
              />
            ))}
          </div>
          <span className="text-xs text-muted-foreground font-body">
            {rating}/5 ({reviews} reviews)
          </span>
        </div>

        <div className="flex items-end justify-between gap-4 mt-auto pt-4 border-t border-border/50">
        <div>
          <span className="font-display text-2xl font-semibold text-primary">
            KSh {price.toLocaleString()}
          </span>
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
              addToCart({
                id: product._id,
                name: product.name,
                price: price,
                rating: rating,
                reviews: reviews,
                description: product.description,
                image: product.image_url
              }, qty); 
              setQty(1); 
            }}
            className="flex items-center gap-2 px-5 py-2.5 bg-gold-gradient text-primary-foreground font-body text-xs font-bold tracking-widest uppercase rounded-sm hover:opacity-90 transition-opacity"
            disabled={!product.in_stock}
          >
            <ShoppingBag className="w-4 h-4" />
            {product.in_stock ? 'Add' : 'Out of Stock'}
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
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/products`)
      .then(res => res.json())
      .then(data => {
        setProducts(data.products || []);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch products:', err);
        setLoading(false);
      });
  }, []);

  return (
    <section id="shop" className="section-spacing">
      <div className="container mx-auto px-4" ref={ref}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={inView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7 }}
          className="text-center mb-16"
        >
          <p className="text-sm tracking-[0.3em] uppercase text-primary font-body mb-4">The Collection</p>
          <h2 className="font-display text-4xl md:text-5xl lg:text-6xl font-light">
            Shop <span className="italic text-gold-gradient">Queen Koba</span>
          </h2>
        </motion.div>

        {loading ? (
          <div className="text-center py-12">Loading products...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {products.map((product, i) => (
              <ProductCard key={product._id} product={product} index={i} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
};

export default ProductStore;
