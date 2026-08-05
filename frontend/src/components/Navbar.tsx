import { useState } from "react";
import { ShoppingBag, Menu, X, User, LogOut } from "lucide-react";
import { useCart } from "@/context/CartContext";
import { useAuth } from "@/context/AuthContext";
import { motion, AnimatePresence } from "framer-motion";
import { Link } from "react-router-dom";

const Navbar = () => {
  const { itemCount, setIsOpen } = useCart();
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  const links = [
    { label: "Home", href: "/" },
    { label: "Shop", href: "/shop" },
    { label: "Our Story", href: "/story" },
    { label: "Contact", href: "/contact" },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-border/50">
      <div className="container mx-auto flex items-center justify-between h-16 md:h-20 px-4">
        <Link to="/" className="flex items-center gap-3">
          <img 
            src="https://www.dropbox.com/scl/fi/9fr8b22db9mlskvvaodqn/kb.jpeg?rlkey=g9sxg31b8d28qgk636a3a024e&st=bt9mn3sn&raw=1" 
            alt="Queen Koba Logo" 
            className="h-10 md:h-12 w-auto object-contain"
          />
          <span className="font-display text-2xl md:text-3xl font-semibold tracking-wide text-primary">
            Queen Koba
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          {links.map((l) => (
            <Link
              key={l.href}
              to={l.href}
              className="text-sm font-body tracking-widest uppercase text-muted-foreground hover:text-primary transition-colors duration-300"
            >
              {l.label}
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-4">
          {user ? (
            <div className="hidden md:flex items-center gap-3">
              <span className="text-sm font-body text-muted-foreground">Hi, {user.name.split(' ')[0]}</span>
              <button
                onClick={logout}
                className="p-2 text-foreground hover:text-primary transition-colors"
                aria-label="Logout"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          ) : (
            <Link
              to="/login"
              className="hidden md:flex items-center gap-2 text-sm font-body text-muted-foreground hover:text-primary transition-colors"
            >
              <User className="w-5 h-5" />
              Sign In
            </Link>
          )}
          <button
            onClick={() => setIsOpen(true)}
            className="relative p-2 text-foreground hover:text-primary transition-colors"
            aria-label="Open cart"
          >
            <ShoppingBag className="w-5 h-5" />
            {itemCount > 0 && (
              <span className="absolute -top-1 -right-1 w-5 h-5 bg-primary text-primary-foreground text-xs font-bold rounded-full flex items-center justify-center">
                {itemCount}
              </span>
            )}
          </button>
          <button
            className="md:hidden p-2 text-foreground"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileOpen(false)}
              className="fixed inset-0 bg-black/70 backdrop-blur-sm z-40 md:hidden"
            />
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 30, stiffness: 300 }}
              className="fixed right-0 top-0 bottom-0 w-64 bg-[#2A2520] border-l-2 border-primary z-50 md:hidden shadow-2xl"
            >
              <div className="flex flex-col h-full">
                <div className="flex items-center justify-between p-4 border-b-2 border-primary/30 bg-[#1F1A17]">
                  <span className="font-display text-xl font-semibold text-[#D4AF37]">Menu</span>
                  <button
                    onClick={() => setMobileOpen(false)}
                    className="p-2 text-[#E5D4B8] hover:text-[#D4AF37] transition-colors"
                    aria-label="Close menu"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
                <div className="flex flex-col px-4 py-6 gap-4 bg-[#1F1A17]">
                  {links.map((l) => (
                    <Link
                      key={l.href}
                      to={l.href}
                      onClick={() => setMobileOpen(false)}
                      className="text-base tracking-widest uppercase text-white hover:text-[#D4AF37] transition-colors py-3 font-bold border-b border-[#3A3530]"
                    >
                      {l.label}
                    </Link>
                  ))}
                  {user ? (
                    <>
                      <div className="text-sm text-[#E5D4B8] py-2 border-b border-[#3A3530]">
                        Hi, {user.name}
                      </div>
                      <button
                        onClick={() => { logout(); setMobileOpen(false); }}
                        className="text-base tracking-widest uppercase text-white hover:text-[#D4AF37] transition-colors py-3 font-bold border-b border-[#3A3530] text-left flex items-center gap-2"
                      >
                        <LogOut className="w-4 h-4" />
                        Sign Out
                      </button>
                    </>
                  ) : (
                    <Link
                      to="/login"
                      onClick={() => setMobileOpen(false)}
                      className="text-base tracking-widest uppercase text-white hover:text-[#D4AF37] transition-colors py-3 font-bold border-b border-[#3A3530] flex items-center gap-2"
                    >
                      <User className="w-4 h-4" />
                      Sign In
                    </Link>
                  )}
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </nav>
  );
};

export default Navbar;
