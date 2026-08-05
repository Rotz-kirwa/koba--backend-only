import { useEffect, useState } from 'react';
import { X, Tag } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

interface Promotion {
  id: string;
  code: string;
  discount: number;
  type: string;
  status: string;
  expires: string | null;
}

export default function PromoPopup() {
  const [showPopup, setShowPopup] = useState(false);
  const [promo, setPromo] = useState<Promotion | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    // Fetch active promotions
    const fetchPromo = async () => {
      try {
        const res = await fetch(`${API_URL}/promotions/active`);
        const data = await res.json();
        if (data.promotions && data.promotions.length > 0) {
          setPromo(data.promotions[0]);
        }
      } catch (err) {
        console.error('Failed to fetch promotions:', err);
      }
    };

    fetchPromo();

    // Show popup after 5 seconds initially
    const initialTimer = setTimeout(() => {
      setShowPopup(true);
    }, 5000);

    // Show popup every 3 minutes
    const interval = setInterval(() => {
      setShowPopup(true);
    }, 180000); // 3 minutes

    return () => {
      clearTimeout(initialTimer);
      clearInterval(interval);
    };
  }, []);

  const handleCopy = () => {
    if (promo) {
      navigator.clipboard.writeText(promo.code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleClose = () => {
    setShowPopup(false);
  };

  if (!promo) return null;

  return (
    <AnimatePresence>
      {showPopup && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={handleClose}
        >
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-white rounded-lg p-8 max-w-md w-full relative shadow-2xl"
          >
            <button
              onClick={handleClose}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
            >
              <X className="w-6 h-6" />
            </button>

            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-[#8B6F47] to-[#6d5638] rounded-full flex items-center justify-center mx-auto mb-4">
                <Tag className="w-8 h-8 text-white" />
              </div>

              <h2 className="text-3xl font-serif font-bold mb-2">
                Special Offer!
              </h2>
              
              <p className="text-gray-600 mb-6">
                {promo.type === 'free_shipping' 
                  ? 'Get Free Shipping on your order!' 
                  : `Get ${promo.discount}% OFF your purchase!`}
              </p>

              <div className="bg-gray-50 border-2 border-dashed border-[#8B6F47] rounded-lg p-4 mb-6">
                <p className="text-sm text-gray-500 mb-2">Use code:</p>
                <p className="text-2xl font-mono font-bold text-[#8B6F47]">
                  {promo.code}
                </p>
              </div>

              <button
                onClick={handleCopy}
                className="w-full bg-gradient-to-r from-[#8B6F47] to-[#6d5638] text-white py-3 rounded-lg font-semibold hover:opacity-90 transition-opacity mb-3"
              >
                {copied ? 'Copied!' : 'Copy Code'}
              </button>

              {promo.expires && (
                <p className="text-xs text-gray-500">
                  Expires: {new Date(promo.expires).toLocaleDateString()}
                </p>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
