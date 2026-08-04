import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, ShoppingCart, Package, Users, CreditCard, LogOut, Menu, X } from 'lucide-react';
import { useState } from 'react';

export default function Sidebar() {
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);

  const links = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/orders', icon: ShoppingCart, label: 'Orders' },
    { to: '/products', icon: Package, label: 'Products' },
    { to: '/users', icon: Users, label: 'Users' },
    { to: '/payments', icon: CreditCard, label: 'Payments' },
  ];

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    window.location.href = '/login';
  };

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="lg:hidden fixed top-4 right-4 z-50 bg-gray-900 text-white p-3 rounded-xl shadow-lg hover:bg-gray-800 transition-colors"
      >
        {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </button>

      {/* Overlay */}
      {isOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-30"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed lg:static inset-y-0 left-0 z-40 w-64 bg-gradient-to-b from-gray-900 to-gray-800 text-white min-h-screen p-6 shadow-2xl transform transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="mb-10 mt-12 lg:mt-0">
          <h2 className="text-2xl font-bold bg-gradient-to-r from-yellow-400 to-yellow-200 bg-clip-text text-transparent">Queen Koba</h2>
          <p className="text-gray-400 text-sm mt-1">Admin Dashboard</p>
        </div>

        <nav className="space-y-1">
          {links.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              onClick={() => setIsOpen(false)}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                location.pathname === link.to
                  ? 'bg-gradient-to-r from-yellow-500 to-yellow-400 text-gray-900 shadow-lg font-semibold'
                  : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
              }`}
            >
              <link.icon className="w-5 h-5" />
              <span>{link.label}</span>
            </Link>
          ))}
        </nav>

        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-4 py-3 rounded-xl text-gray-300 hover:bg-red-500/20 hover:text-red-400 w-full mt-8 transition-all duration-200"
        >
          <LogOut className="w-5 h-5" />
          <span>Logout</span>
        </button>
      </div>
    </>
  );
}
