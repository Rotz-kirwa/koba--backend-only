import { useState, useEffect } from 'react';
import { adminAPI } from '@/lib/api';
import { Plus, Edit, Trash2 } from 'lucide-react';

export default function Products() {
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      const data = await adminAPI.getProducts();
      setProducts(
        data.map((product: any) => ({
          id: product.id || product._id,
          name: product.name,
          price: product.price ?? Math.round((product.base_price_usd || 0) * 128.5),
          description: product.description,
          image: product.image || product.image_url || 'https://via.placeholder.com/300',
        }))
      );
    } catch (error) {
      console.error('Failed to load products:', error);
      // Fallback mock data
      setProducts([
        { id: '1', name: 'Eternal Radiance Cleanser', price: 1500, description: 'Gentle cleanser', image: 'https://via.placeholder.com/300' },
        { id: '2', name: 'Eternal Radiance Toner', price: 1800, description: 'Balancing toner', image: 'https://via.placeholder.com/300' },
        { id: '3', name: 'Eternal Radiance Serum', price: 2500, description: 'Brightening serum', image: 'https://via.placeholder.com/300' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const deleteProduct = async (id: string) => {
    if (!confirm('Delete this product?')) return;
    try {
      await adminAPI.deleteProduct(id);
      loadProducts();
    } catch (error) {
      console.error('Failed to delete product:', error);
    }
  };

  if (loading) return <div className="p-4 lg:p-8 pt-20 lg:pt-8">Loading...</div>;

  return (
    <div className="p-4 lg:p-8 pt-20 lg:pt-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6 lg:mb-8">
        <h1 className="text-2xl lg:text-3xl font-bold">Products Management</h1>
        <button
          onClick={() => alert('Product creation UI is not implemented yet. Use API directly for now.')}
          className="bg-blue-500 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-600 text-sm lg:text-base w-full sm:w-auto justify-center"
        >
          <Plus className="w-4 h-4" />
          Add Product
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
        {products.map((product) => (
          <div key={product.id} className="bg-white rounded-lg shadow p-4 lg:p-6">
            <img src={product.image} alt={product.name} className="w-full h-40 lg:h-48 object-cover rounded mb-4" />
            <h3 className="font-bold text-base lg:text-lg mb-2">{product.name}</h3>
            <p className="text-gray-600 text-xs lg:text-sm mb-4 line-clamp-2">{product.description}</p>
            <div className="flex justify-between items-center">
              <span className="text-lg lg:text-xl font-bold">KSh {product.price.toLocaleString()}</span>
              <div className="flex gap-2">
                <button
                  onClick={() => alert('Product editing UI is not implemented yet. Use API directly for now.')}
                  className="p-2 text-blue-500 hover:bg-blue-50 rounded"
                >
                  <Edit className="w-4 h-4" />
                </button>
                <button
                  onClick={() => deleteProduct(product.id)}
                  className="p-2 text-red-500 hover:bg-red-50 rounded"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
