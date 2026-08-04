const WhatsAppFloat = () => {
  const phoneNumber = "254119559180";
  const message = "Hi Queen Koba! I'm interested in your products.";
  const whatsappUrl = `https://wa.me/${phoneNumber}?text=${encodeURIComponent(message)}`;

  return (
    <a
      href={whatsappUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="fixed bottom-8 right-8 z-50 group"
      aria-label="Chat on WhatsApp"
    >
      {/* Ripple effect */}
      <div className="absolute inset-0 rounded-full bg-[#25D366] animate-ping opacity-20" />
      
      {/* Main button container */}
      <div className="relative">
        {/* Shadow layer */}
        <div className="absolute inset-0 bg-[#25D366] rounded-full blur-md opacity-60 group-hover:opacity-80 transition-opacity" />
        
        {/* Button */}
        <div className="relative w-16 h-16 bg-[#25D366] rounded-full flex items-center justify-center transform transition-all duration-300 group-hover:scale-110 group-hover:bg-[#20BA5A] shadow-2xl">
          {/* WhatsApp Logo SVG */}
          <svg
            viewBox="0 0 32 32"
            className="w-9 h-9 fill-white"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M16 0C7.164 0 0 7.164 0 16c0 2.825.738 5.488 2.031 7.794L0 32l8.394-2.031C10.7 31.262 13.363 32 16 32c8.836 0 16-7.164 16-16S24.836 0 16 0zm0 29.333c-2.544 0-4.944-.706-6.981-1.931l-.5-.3-5.181 1.256 1.256-5.181-.3-.5C2.706 20.944 2 18.544 2 16 2 8.28 8.28 2 16 2s14 6.28 14 14-6.28 13.333-14 13.333z" />
            <path d="M23.738 19.425c-.4-.2-2.363-1.169-2.731-1.3-.369-.131-.637-.2-.906.2-.269.4-1.038 1.3-1.275 1.569-.237.269-.475.3-.875.1-.4-.2-1.688-.625-3.213-1.988-1.188-1.063-1.988-2.375-2.219-2.775-.231-.4-.025-.619.175-.819.181-.181.4-.475.6-.713.2-.237.269-.4.4-.669.131-.269.069-.5-.031-.7-.1-.2-.906-2.188-1.244-2.994-.331-.788-.662-.681-.906-.694-.237-.012-.506-.012-.775-.012s-.712.1-1.087.5c-.375.4-1.431 1.4-1.431 3.413s1.463 3.956 1.669 4.225c.206.269 2.9 4.431 7.025 6.213.981.425 1.75.681 2.35.869.988.313 1.888.269 2.6.163.794-.119 2.363-.969 2.694-1.906.331-.938.331-1.738.231-1.906-.1-.169-.369-.269-.769-.469z" />
          </svg>
        </div>
        
        {/* Notification badge */}
        <div className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 border-3 border-white rounded-full flex items-center justify-center shadow-lg">
          <span className="text-white text-xs font-bold">1</span>
        </div>
      </div>
      
      {/* Tooltip */}
      <div className="absolute right-full mr-4 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-all duration-300 pointer-events-none">
        <div className="bg-white text-gray-800 px-4 py-3 rounded-xl shadow-2xl whitespace-nowrap border border-gray-200">
          <p className="text-sm font-semibold">💬 Need help?</p>
          <p className="text-xs text-gray-600 mt-1">Chat with us on WhatsApp</p>
        </div>
        {/* Arrow */}
        <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-full">
          <div className="w-0 h-0 border-t-[8px] border-t-transparent border-b-[8px] border-b-transparent border-l-[8px] border-l-white" />
        </div>
      </div>
    </a>
  );
};

export default WhatsAppFloat;
