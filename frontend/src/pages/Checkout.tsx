import { useState, useEffect } from "react";
import { useCart } from "@/context/CartContext";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { CreditCard, Smartphone, Building2, CheckCircle2, ArrowLeft } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { paymentAPI, ordersAPI } from "@/lib/api";

const getPaymentIcon = (type: string) => {
  if (type.includes('card') || type.includes('visa') || type.includes('mastercard')) return CreditCard;
  if (type.includes('bank') || type.includes('transfer')) return Building2;
  return Smartphone;
};

interface PaymentMethod {
  id: string;
  name: string;
  type: string;
  description: string;
  logo?: string;
}

const paymentLogos: Record<string, string> = {
  mpesa: "https://pbs.twimg.com/ext_tw_video_thumb/1181852139011936256/pu/img/1UCUl2bSj2RCyq6H.jpg",
  airtel_money: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQzoFx31kmrStLhhxN53irFXTILQ93sX9hkSQ&s",
  card: "https://i.pinimg.com/736x/bd/16/2c/bd162c26d6a49bbd39126cd9e5e79d19.jpg",
  bank_transfer: "https://i.pinimg.com/736x/9b/3d/bd/9b3dbd2bce3d86a3d63a79b1ecf86b4e.jpg",
  mtn_mobile_money: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSGvdmkSOboNGNU79JdQJe3lvmojdN64iSfwQ&s",
  ecocash: "https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/EcoCash_Logo.svg/1200px-EcoCash_Logo.svg.png",
  lumicash: "https://play-lh.googleusercontent.com/9XKZHKBLqsLYYqJYYqJYYqJYYqJYYqJYYqJYYqJYYqJYYqJYYqJYYqJYYqJYYqJYYqJY",
  orange_money: "https://i.pinimg.com/736x/e6/b1/69/e6b169c06abd09abf3e54dfb5b1a1abd.jpg",
  vodacom_mpesa: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRkc_60sjm9kRnV0NNknGFr4YHywQ4dy5J9xA&s",
};

const currencyConfig: Record<string, { code: string; symbol: string; rate: number }> = {
  Kenya: { code: "KES", symbol: "KSh", rate: 1 },
  Uganda: { code: "UGX", symbol: "UGX", rate: 28.5 },
  Burundi: { code: "BIF", symbol: "FBu", rate: 285 },
  Congo: { code: "CDF", symbol: "FC", rate: 280 },
};

const formatCurrency = (amount: number, country: string) => {
  const config = currencyConfig[country];
  const converted = Math.round(amount * config.rate);
  return `${config.symbol} ${converted.toLocaleString()}`;
};

const getFallbackMethods = (country: string): PaymentMethod[] => {
  const methods: Record<string, PaymentMethod[]> = {
    Kenya: [
      { id: "mpesa", name: "M-Pesa", type: "mobile_money", description: "Mobile money (most popular in Kenya)", logo: paymentLogos.mpesa },
      { id: "airtel_money", name: "Airtel Money", type: "mobile_money", description: "Mobile money alternative", logo: paymentLogos.airtel_money },
      { id: "card", name: "Visa/Mastercard", type: "card", description: "Credit/Debit cards", logo: paymentLogos.card },
      { id: "bank_transfer", name: "Bank Transfer", type: "bank_transfer", description: "Direct bank transfer", logo: paymentLogos.bank_transfer },
    ],
    Uganda: [
      { id: "mtn_mobile_money", name: "MTN Mobile Money", type: "mobile_money", description: "Primary mobile money service", logo: paymentLogos.mtn_mobile_money },
      { id: "airtel_money", name: "Airtel Money", type: "mobile_money", description: "Alternative mobile money", logo: paymentLogos.airtel_money },
      { id: "card", name: "Visa/Mastercard", type: "card", description: "Credit/Debit cards", logo: paymentLogos.card },
    ],
    Burundi: [
      { id: "lumicash", name: "Lumicash", type: "mobile_money", description: "Mobile money service", logo: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTa2EsR4opmeHo-7AZdQWOXzAopmCAtyTWJbA&s" },
      { id: "ecocash", name: "EcoCash", type: "mobile_money", description: "Mobile payment platform", logo: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRxM9aLsK9Xzy2xfcGjsciN7ge8p8KdzqhvOA&s" },
      { id: "bank_transfer", name: "Bank Transfer", type: "bank_transfer", description: "Direct bank transfer", logo: paymentLogos.bank_transfer },
    ],
    Congo: [
      { id: "orange_money", name: "Orange Money", type: "mobile_money", description: "Mobile money service", logo: paymentLogos.orange_money },
      { id: "vodacom_mpesa", name: "Vodacom M-Pesa", type: "mobile_money", description: "Mobile money platform", logo: paymentLogos.vodacom_mpesa },
      { id: "bank_transfer", name: "Bank Transfer", type: "bank_transfer", description: "Direct bank transfer", logo: paymentLogos.bank_transfer },
    ],
  };
  return methods[country] || methods.Kenya;
}

const Checkout = () => {
  const { items, total, clearCart } = useCart();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [step, setStep] = useState(1);
  const [country, setCountry] = useState("Kenya");
  const [paymentMethod, setPaymentMethod] = useState("");
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [loading, setLoading] = useState(false);
  const [paymentDetails, setPaymentDetails] = useState({
    phoneNumber: "",
    cardNumber: "",
    cardExpiry: "",
    cardCvv: "",
    accountNumber: "",
    bankName: "",
  });
  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    phone: "",
    address: "",
    city: "",
    postalCode: "",
  });

  useEffect(() => {
    const fetchPaymentMethods = async () => {
      // Start with fallback methods immediately
      const fallbackMethods = getFallbackMethods(country);
      setPaymentMethods(fallbackMethods);
      
      try {
        setLoading(true);
        const response = await paymentAPI.getByCountry(country);
        const methods = Array.isArray(response) ? response : response?.payment_methods || [];
        if (methods.length > 0) {
          setPaymentMethods(methods);
        }
        setPaymentMethod("");
      } catch (error) {
        console.error('Failed to fetch payment methods:', error);
        // Keep fallback methods already set
      } finally {
        setLoading(false);
      }
    };
    fetchPaymentMethods();
  }, [country]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handlePaymentInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setPaymentDetails({ ...paymentDetails, [e.target.name]: e.target.value });
  };

  const getPaymentMethodType = () => {
    const method = paymentMethods.find(m => m.id === paymentMethod);
    if (!method) return null;
    if (method.type === 'card') return 'card';
    if (method.type === 'bank_transfer') return 'bank';
    return 'mobile';
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      
      // Simulate payment processing
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      toast({
        title: "Order Placed Successfully!",
        description: `Your order of ${formatCurrency(total, country)} has been received. You will receive a payment prompt shortly.`,
      });
      
      clearCart();
      setTimeout(() => navigate("/shop"), 2000);
    } catch (error) {
      console.error('Order submission failed:', error);
      toast({
        title: "Order Failed",
        description: "Failed to place order. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  if (items.length === 0) {
    return (
      <div className="min-h-screen pt-32 pb-20">
        <div className="container mx-auto px-4 text-center">
          <h1 className="font-display text-4xl mb-4">Your cart is empty</h1>
          <button
            onClick={() => navigate("/shop")}
            className="inline-flex items-center gap-2 px-6 py-3 bg-gold-gradient text-primary-foreground font-body font-semibold text-sm tracking-widest uppercase rounded-sm"
          >
            Continue Shopping
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-24 pb-20 bg-secondary/20">
      <div className="container mx-auto px-4 max-w-6xl">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-muted-foreground hover:text-primary transition-colors mb-8"
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="font-body text-sm tracking-wide uppercase">Back</span>
        </button>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Progress Steps */}
            <div className="flex items-center justify-between mb-8">
              {[1, 2, 3, 4].map((s) => (
                <div key={s} className="flex items-center flex-1">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-body font-bold ${
                      step >= s ? "bg-gold-gradient text-primary-foreground" : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {step > s ? <CheckCircle2 className="w-5 h-5" /> : s}
                  </div>
                  {s < 4 && (
                    <div className={`flex-1 h-1 mx-2 ${step > s ? "bg-primary" : "bg-muted"}`} />
                  )}
                </div>
              ))}
            </div>

            {/* Step 1: Shipping Information */}
            {step === 1 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="luxury-card"
              >
                <h2 className="font-display text-3xl font-semibold mb-6">Shipping Information</h2>
                <div className="space-y-4">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-body mb-2">Full Name *</label>
                      <input
                        type="text"
                        name="fullName"
                        value={formData.fullName}
                        onChange={handleInputChange}
                        className="w-full px-4 py-3 bg-background border border-border rounded-sm focus:outline-none focus:border-primary"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-body mb-2">Email *</label>
                      <input
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={handleInputChange}
                        className="w-full px-4 py-3 bg-background border border-border rounded-sm focus:outline-none focus:border-primary"
                        required
                      />
                    </div>
                  </div>
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-body mb-2">Phone Number *</label>
                      <input
                        type="tel"
                        name="phone"
                        value={formData.phone}
                        onChange={handleInputChange}
                        className="w-full px-4 py-3 bg-background border border-border rounded-sm focus:outline-none focus:border-primary"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-body mb-2">Country *</label>
                      <select
                        value={country}
                        onChange={(e) => setCountry(e.target.value)}
                        className="w-full px-4 py-3 bg-background border border-border rounded-sm focus:outline-none focus:border-primary"
                      >
                        <option value="Kenya">Kenya</option>
                        <option value="Uganda">Uganda</option>
                        <option value="Burundi">Burundi</option>
                        <option value="Congo">DR Congo</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-body mb-2">Address *</label>
                    <input
                      type="text"
                      name="address"
                      value={formData.address}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 bg-background border border-border rounded-sm focus:outline-none focus:border-primary"
                      required
                    />
                  </div>
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-body mb-2">City *</label>
                      <input
                        type="text"
                        name="city"
                        value={formData.city}
                        onChange={handleInputChange}
                        className="w-full px-4 py-3 bg-background border border-border rounded-sm focus:outline-none focus:border-primary"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-body mb-2">Postal Code</label>
                      <input
                        type="text"
                        name="postalCode"
                        value={formData.postalCode}
                        onChange={handleInputChange}
                        className="w-full px-4 py-3 bg-background border border-border rounded-sm focus:outline-none focus:border-primary"
                      />
                    </div>
                  </div>
                  <button
                    onClick={() => setStep(2)}
                    className="w-full py-4 bg-gold-gradient text-primary-foreground font-body font-bold text-sm tracking-widest uppercase rounded-sm hover:opacity-90 transition-opacity"
                  >
                    Continue to Payment
                  </button>
                </div>
              </motion.div>
            )}

            {/* Step 2: Payment Method */}
            {step === 2 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="luxury-card"
              >
                <h2 className="font-display text-3xl font-semibold mb-6">Payment Method</h2>
                <p className="text-muted-foreground font-body mb-6">Select your preferred payment method for {country}</p>
                {loading ? (
                  <div className="text-center py-8">
                    <p className="text-muted-foreground font-body">Loading payment methods...</p>
                  </div>
                ) : (
                  <div className="grid md:grid-cols-2 gap-4 mb-6">
                    {paymentMethods.map((method) => (
                      <button
                        key={method.id}
                        onClick={() => setPaymentMethod(method.id)}
                        className={`relative h-32 border-4 rounded-lg overflow-hidden transition-all ${
                          paymentMethod === method.id
                            ? "border-primary ring-4 ring-primary/30"
                            : "border-border hover:border-primary/50"
                        }`}
                      >
                        <img 
                          src={method.logo} 
                          alt={method.name} 
                          className="w-full h-full object-cover"
                        />
                        {paymentMethod === method.id && (
                          <div className="absolute inset-0 bg-primary/20 flex items-center justify-center">
                            <CheckCircle2 className="w-12 h-12 text-primary drop-shadow-lg" />
                          </div>
                        )}
                      </button>
                    ))}
                  </div>
                )}
                <div className="flex gap-4">
                  <button
                    onClick={() => setStep(1)}
                    className="flex-1 py-4 border border-border text-foreground font-body font-bold text-sm tracking-widest uppercase rounded-sm hover:bg-secondary transition-colors"
                  >
                    Back
                  </button>
                  <button
                    onClick={() => setStep(3)}
                    disabled={!paymentMethod}
                    className="flex-1 py-4 bg-gold-gradient text-primary-foreground font-body font-bold text-sm tracking-widest uppercase rounded-sm hover:opacity-90 transition-opacity disabled:opacity-50"
                  >
                    Continue to Payment
                  </button>
                </div>
              </motion.div>
            )}

            {/* Step 3: Payment Details */}
            {step === 3 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="luxury-card"
              >
                <h2 className="font-display text-3xl font-semibold mb-6">Payment Details</h2>
                <p className="text-muted-foreground font-body mb-6">
                  {paymentMethods.find(m => m.id === paymentMethod)?.name}
                </p>

                {/* Mobile Money Payment */}
                {getPaymentMethodType() === 'mobile' && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-body mb-2">Phone Number *</label>
                      <input
                        type="tel"
                        name="phoneNumber"
                        value={paymentDetails.phoneNumber}
                        onChange={handlePaymentInputChange}
                        placeholder="e.g. 254712345678"
                        className="w-full px-4 py-3 bg-background border border-border rounded-sm focus:outline-none focus:border-primary"
                        required
                      />
                      <p className="text-xs text-muted-foreground mt-2">You will receive a payment prompt on this number</p>
                    </div>
                  </div>
                )}

                {/* Card Payment */}
                {getPaymentMethodType() === 'card' && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-body mb-2">Card Number *</label>
                      <input
                        type="text"
                        name="cardNumber"
                        value={paymentDetails.cardNumber}
                        onChange={handlePaymentInputChange}
                        placeholder="1234 5678 9012 3456"
                        maxLength={19}
                        className="w-full px-4 py-3 bg-background border border-border rounded-sm focus:outline-none focus:border-primary"
                        required
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-body mb-2">Expiry Date *</label>
                        <input
                          type="text"
                          name="cardExpiry"
                          value={paymentDetails.cardExpiry}
                          onChange={handlePaymentInputChange}
                          placeholder="MM/YY"
                          maxLength={5}
                          className="w-full px-4 py-3 bg-background border border-border rounded-sm focus:outline-none focus:border-primary"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-body mb-2">CVV *</label>
                        <input
                          type="text"
                          name="cardCvv"
                          value={paymentDetails.cardCvv}
                          onChange={handlePaymentInputChange}
                          placeholder="123"
                          maxLength={4}
                          className="w-full px-4 py-3 bg-background border border-border rounded-sm focus:outline-none focus:border-primary"
                          required
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Bank Transfer */}
                {getPaymentMethodType() === 'bank' && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-body mb-2">Bank Name *</label>
                      <select
                        name="bankName"
                        value={paymentDetails.bankName}
                        onChange={handlePaymentInputChange}
                        className="w-full px-4 py-3 bg-background border border-border rounded-sm focus:outline-none focus:border-primary"
                        required
                      >
                        <option value="">Select your bank</option>
                        <option value="equity">Equity Bank</option>
                        <option value="kcb">KCB Bank</option>
                        <option value="coop">Co-operative Bank</option>
                        <option value="absa">ABSA Bank</option>
                        <option value="stanbic">Stanbic Bank</option>
                        <option value="other">Other</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-body mb-2">Account Number *</label>
                      <input
                        type="text"
                        name="accountNumber"
                        value={paymentDetails.accountNumber}
                        onChange={handlePaymentInputChange}
                        placeholder="Enter your account number"
                        className="w-full px-4 py-3 bg-background border border-border rounded-sm focus:outline-none focus:border-primary"
                        required
                      />
                    </div>
                    <div className="bg-secondary/50 p-4 rounded-sm">
                      <p className="text-sm font-body text-muted-foreground">
                        You will receive bank transfer instructions via email after placing your order.
                      </p>
                    </div>
                  </div>
                )}

                <div className="flex gap-4 mt-6">
                  <button
                    onClick={() => setStep(2)}
                    className="flex-1 py-4 border border-border text-foreground font-body font-bold text-sm tracking-widest uppercase rounded-sm hover:bg-secondary transition-colors"
                  >
                    Back
                  </button>
                  <button
                    onClick={() => setStep(4)}
                    className="flex-1 py-4 bg-gold-gradient text-primary-foreground font-body font-bold text-sm tracking-widest uppercase rounded-sm hover:opacity-90 transition-opacity"
                  >
                    Review Order
                  </button>
                </div>
              </motion.div>
            )}

            {/* Step 4: Review & Confirm */}
            {step === 4 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="luxury-card"
              >
                <h2 className="font-display text-3xl font-semibold mb-6">Review Your Order</h2>
                <div className="space-y-6">
                  <div>
                    <h3 className="font-display text-xl font-semibold mb-3">Shipping Details</h3>
                    <div className="text-sm font-body space-y-1 text-muted-foreground">
                      <p>{formData.fullName}</p>
                      <p>{formData.email}</p>
                      <p>{formData.phone}</p>
                      <p>{formData.address}</p>
                      <p>{formData.city}, {country}</p>
                    </div>
                  </div>
                  <div>
                    <h3 className="font-display text-xl font-semibold mb-3">Payment Method</h3>
                    <p className="text-sm font-body text-muted-foreground mb-1">
                      {paymentMethods.find(m => m.id === paymentMethod)?.name}
                    </p>
                    {getPaymentMethodType() === 'mobile' && paymentDetails.phoneNumber && (
                      <p className="text-sm font-body text-muted-foreground">Phone: {paymentDetails.phoneNumber}</p>
                    )}
                    {getPaymentMethodType() === 'card' && paymentDetails.cardNumber && (
                      <p className="text-sm font-body text-muted-foreground">Card: **** **** **** {paymentDetails.cardNumber.slice(-4)}</p>
                    )}
                    {getPaymentMethodType() === 'bank' && paymentDetails.bankName && (
                      <p className="text-sm font-body text-muted-foreground">Bank: {paymentDetails.bankName}</p>
                    )}
                  </div>
                  <div className="flex gap-4">
                    <button
                      onClick={() => setStep(3)}
                      className="flex-1 py-4 border border-border text-foreground font-body font-bold text-sm tracking-widest uppercase rounded-sm hover:bg-secondary transition-colors"
                    >
                      Back
                    </button>
                    <button
                      onClick={handleSubmit}
                      disabled={loading}
                      className="flex-1 py-4 bg-gold-gradient text-primary-foreground font-body font-bold text-sm tracking-widest uppercase rounded-sm hover:opacity-90 transition-opacity disabled:opacity-50"
                    >
                      {loading ? "Processing..." : "Place Order"}
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </div>

          {/* Order Summary Sidebar */}
          <div className="lg:col-span-1">
            <div className="luxury-card sticky top-24">
              <h3 className="font-display text-2xl font-semibold mb-6">Order Summary</h3>
              <div className="space-y-4 mb-6">
                {items.map((item) => (
                  <div key={item.product.id} className="flex gap-4 pb-4 border-b border-border/50">
                    <div className="flex-1">
                      <h4 className="font-display text-sm font-semibold mb-1">{item.product.name}</h4>
                      <p className="text-xs text-muted-foreground font-body">Qty: {item.quantity}</p>
                    </div>
                    <p className="font-body text-sm font-semibold">
                      {formatCurrency(item.product.price * item.quantity, country)}
                    </p>
                  </div>
                ))}
              </div>
              <div className="space-y-3 pt-4 border-t border-border">
                <div className="flex justify-between font-body text-sm">
                  <span className="text-muted-foreground">Subtotal</span>
                  <span>{formatCurrency(total, country)}</span>
                </div>
                <div className="flex justify-between font-body text-sm">
                  <span className="text-muted-foreground">Shipping</span>
                  <span className="text-primary">{total >= 5000 ? "FREE" : formatCurrency(500, country)}</span>
                </div>
                <div className="flex justify-between font-display text-xl font-semibold pt-3 border-t border-border">
                  <span>Total</span>
                  <span className="text-primary">{formatCurrency(total >= 5000 ? total : total + 500, country)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Checkout;
