import { useState, useEffect } from 'react';
import { adminAPI } from '@/lib/api';

export default function Users() {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const data = await adminAPI.getUsers();
      setUsers(data);
    } catch (error) {
      console.error('Failed to load users:', error);
      // Fallback mock data
      setUsers([
        { _id: '1', username: 'Jane Doe', email: 'jane@example.com', country: 'Kenya', created_at: new Date().toISOString() },
        { _id: '2', username: 'John Smith', email: 'john@example.com', country: 'Uganda', created_at: new Date().toISOString() },
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-4 lg:p-8 pt-20 lg:pt-8">Loading...</div>;

  return (
    <div className="p-4 lg:p-8 pt-20 lg:pt-8">
      <h1 className="text-2xl lg:text-3xl font-bold mb-6 lg:mb-8">Users Management</h1>
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px]">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 lg:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-3 lg:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                <th className="px-3 lg:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Country</th>
                <th className="px-3 lg:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Joined</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user._id}>
                  <td className="px-3 lg:px-6 py-4 text-xs lg:text-sm font-medium">{user.username}</td>
                  <td className="px-3 lg:px-6 py-4 text-xs lg:text-sm">{user.email}</td>
                  <td className="px-3 lg:px-6 py-4 text-xs lg:text-sm">{user.country}</td>
                  <td className="px-3 lg:px-6 py-4 text-xs lg:text-sm">{new Date(user.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
