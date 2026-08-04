const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const apiClient = async (endpoint: string, options: RequestInit = {}) => {
  const token = localStorage.getItem('admin_token');
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || data.error || 'API request failed');
  }

  return data;
};

export const adminAPI = {
  login: (credentials: { email: string; password: string }) =>
    apiClient('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    }),

  getStats: () => apiClient('/admin/stats'),
  getOrders: () => apiClient('/admin/orders'),
  getOrder: (id: string) => apiClient(`/admin/orders/${id}`),
  updateOrderStatus: (id: string, status: string) =>
    apiClient(`/admin/orders/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),

  getProducts: async () => {
    const data = await apiClient('/products');
    return data.products || [];
  },
  createProduct: (product: any) =>
    apiClient('/admin/products', {
      method: 'POST',
      body: JSON.stringify(product),
    }),
  updateProduct: (id: string, product: any) =>
    apiClient(`/admin/products/${id}`, {
      method: 'PUT',
      body: JSON.stringify(product),
    }),
  deleteProduct: (id: string) =>
    apiClient(`/admin/products/${id}`, { method: 'DELETE' }),

  getUsers: () => apiClient('/admin/users'),
  getPayments: () => apiClient('/admin/payments'),
};

export default adminAPI;
