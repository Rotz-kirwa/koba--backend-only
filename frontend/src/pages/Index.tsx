import Hero from "@/components/Hero";
import BrandStory from "@/components/BrandStory";
import BenefitsSection from "@/components/BenefitsSection";
import IngredientsSpotlight from "@/components/IngredientsSpotlight";
import ProductStore from "@/components/ProductStore";
import Testimonials from "@/components/Testimonials";
import SafetyDisclaimer from "@/components/SafetyDisclaimer";
import FinalCTA from "@/components/FinalCTA";
import Footer from "@/components/Footer";

const Index = () => {
  return (
    <main>
      <Hero />
      <BrandStory />
      <BenefitsSection />
      <IngredientsSpotlight />
      <ProductStore />
      <Testimonials />
      <SafetyDisclaimer />
      <FinalCTA />
      <Footer />
    </main>
  );
};

export default Index;
