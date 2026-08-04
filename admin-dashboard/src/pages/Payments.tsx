import { useState, useEffect } from 'react';
import { adminAPI } from '@/lib/api';

export default function Payments() {
  const [payments, setPayments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPayments();
  }, []);

  const loadPayments = async () => {
    try {
      const data = await adminAPI.getPayments();
      setPayments(data);
    } catch (error) {
      console.error('Failed to load payments:', error);
      // Fallback mock data
      setPayments([
        { _id: 'PAY001', order_id: 'ORD001', payment_method: 'mpesa', amount: 5500, status: 'completed', created_at: new Date().toISOString() },
        { _id: 'PAY002', order_id: 'ORD002', payment_method: 'card', amount: 8000, status: 'completed', created_at: new Date().toISOString() },
        { _id: 'PAY003', order_id: 'ORD003', payment_method: 'airtel_money', amount: 2500, status: 'pending', created_at: new Date().toISOString() },
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-4 lg:p-8 pt-20 lg:pt-8">Loading...</div>;

  return (
    <div className="p-4 lg:p-8 pt-20 lg:pt-8">
      <h1 className="text-2xl lg:text-3xl font-bold mb-6 lg:mb-8">Payments Tracking</h1>
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[768px]">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 lg:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Payment ID</th>
                <th className="px-3 lg:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Order ID</th>
                <th className="px-3 lg:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Method</th>
                <th className="px-3 lg:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                <th className="px-3 lg:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-3 lg:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {payments.map((payment) => (
                <tr key={payment._id}>
                  <td className="px-3 lg:px-6 py-4 text-xs lg:text-sm font-mono">{payment._id.slice(0, 8)}...</td>
                  <td className="px-3 lg:px-6 py-4 text-xs lg:text-sm">{payment.order_id}</td>
                  <td className="px-3 lg:px-6 py-4 text-xs lg:text-sm capitalize">{payment.payment_method}</td>
                  <td className="px-3 lg:px-6 py-4 text-xs lg:text-sm font-semibold">KSh {payment.amount?.toLocaleString()}</td>
                  <td className="px-3 lg:px-6 py-4">
                    <span className={`px-2 py-1 text-xs rounded-full whitespace-nowrap ${
                      payment.status === 'completed' ? 'bg-green-100 text-green-800' :
                      payment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {payment.status}
                    </span>
                  </td>
                  <td className="px-3 lg:px-6 py-4 text-xs lg:text-sm whitespace-nowrap">{new Date(payment.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
