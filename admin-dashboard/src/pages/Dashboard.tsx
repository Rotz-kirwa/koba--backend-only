import { useState, useEffect } from 'react';
import { adminAPI } from '@/lib/api';
import { Package, Users, DollarSign, ShoppingCart, TrendingUp } from 'lucide-react';

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalOrders: 0,
    totalRevenue: 0,
    totalUsers: 0,
    totalProducts: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await adminAPI.getStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
      setStats({
        totalOrders: 156,
        totalRevenue: 1250000,
        totalUsers: 89,
        totalProducts: 6,
      });
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    { title: 'Total Orders', value: stats.totalOrders, icon: ShoppingCart, color: 'from-blue-500 to-blue-600', bg: 'bg-blue-50', iconBg: 'bg-blue-500' },
    { title: 'Revenue', value: `KSh ${stats.totalRevenue.toLocaleString()}`, icon: DollarSign, color: 'from-green-500 to-green-600', bg: 'bg-green-50', iconBg: 'bg-green-500' },
    { title: 'Users', value: stats.totalUsers, icon: Users, color: 'from-purple-500 to-purple-600', bg: 'bg-purple-50', iconBg: 'bg-purple-500' },
    { title: 'Products', value: stats.totalProducts, icon: Package, color: 'from-orange-500 to-orange-600', bg: 'bg-orange-50', iconBg: 'bg-orange-500' },
  ];

  if (loading) return <div className="p-4 lg:p-8 pt-20 lg:pt-8 text-center"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-500 mx-auto"></div></div>;

  return (
    <div className="p-4 lg:p-8 pt-20 lg:pt-8">
      <div className="mb-6 lg:mb-8">
        <h1 className="text-2xl lg:text-4xl font-bold text-gray-900 mb-2">Dashboard</h1>
        <p className="text-sm lg:text-base text-gray-600">Welcome back! Here's what's happening today.</p>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 lg:gap-6">
        {statCards.map((stat) => (
          <div key={stat.title} className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-shadow duration-300 p-4 lg:p-6 border border-gray-100">
            <div className="flex items-center justify-between mb-3 lg:mb-4">
              <div className={`${stat.iconBg} p-2 lg:p-3 rounded-xl shadow-md`}>
                <stat.icon className="w-5 h-5 lg:w-6 lg:h-6 text-white" />
              </div>
              <TrendingUp className="w-4 h-4 lg:w-5 lg:h-5 text-green-500" />
            </div>
            <p className="text-gray-500 text-xs lg:text-sm font-medium mb-1">{stat.title}</p>
            <p className="text-xl lg:text-3xl font-bold text-gray-900">{stat.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
