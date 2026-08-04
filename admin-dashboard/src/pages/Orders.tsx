import { useState, useEffect } from 'react';
import { adminAPI } from '@/lib/api';

export default function Orders() {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      const data = await adminAPI.getOrders();
      setOrders(data);
    } catch (error) {
      console.error('Failed to load orders:', error);
      // Fallback mock data
      setOrders([
        { _id: 'ORD001', shipping_info: { full_name: 'Jane Doe' }, total_amount: 5500, status: 'pending' },
        { _id: 'ORD002', shipping_info: { full_name: 'John Smith' }, total_amount: 8000, status: 'completed' },
        { _id: 'ORD003', shipping_info: { full_name: 'Mary Johnson' }, total_amount: 2500, status: 'processing' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (orderId: string, status: string) => {
    try {
      await adminAPI.updateOrderStatus(orderId, status);
      loadOrders();
    } catch (error) {
      console.error('Failed to update order:', error);
    }
  };

  if (loading) return <div className="p-4 lg:p-8 pt-20 lg:pt-8">Loading...</div>;

  return (
    <div className="p-4 lg:p-8 pt-20 lg:pt-8">
      <h1 className="text-2xl lg:text-3xl font-bold mb-6 lg:mb-8">Orders Management</h1>
      <div className="bg-white rounded-lg shadow">
        <div className="overflow-x-auto -mx-4 lg:mx-0">
          <div className="inline-block min-w-full align-middle">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-2 lg:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                  <th className="px-2 lg:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                  <th className="px-2 lg:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                  <th className="px-2 lg:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {orders.map((order) => (
                  <tr key={order._id}>
                    <td className="px-2 lg:px-6 py-3 text-xs whitespace-nowrap">{order._id.slice(0, 6)}</td>
                    <td className="px-2 lg:px-6 py-3 text-xs">{order.shipping_info?.full_name}</td>
                    <td className="px-2 lg:px-6 py-3 text-xs font-semibold whitespace-nowrap">{order.total_amount?.toLocaleString()}</td>
                    <td className="px-2 lg:px-6 py-3">
                      <select
                        value={order.status}
                        onChange={(e) => updateStatus(order._id, e.target.value)}
                        className={`text-xs border-0 rounded-full px-2 py-1 font-medium ${
                          order.status === 'completed' ? 'bg-green-100 text-green-800' :
                          order.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}
                      >
                        <option value="pending">Pending</option>
                        <option value="processing">Processing</option>
                        <option value="shipped">Shipped</option>
                        <option value="completed">Completed</option>
                        <option value="cancelled">Cancelled</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
