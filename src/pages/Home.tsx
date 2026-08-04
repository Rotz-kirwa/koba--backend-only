import Hero from "@/components/Hero";
import BrandStory from "@/components/BrandStory";
import BenefitsSection from "@/components/BenefitsSection";
import Testimonials from "@/components/Testimonials";
import IngredientsSpotlight from "@/components/IngredientsSpotlight";
import SafetyDisclaimer from "@/components/SafetyDisclaimer";
import FinalCTA from "@/components/FinalCTA";

const Home = () => {
  return (
    <main>
      <Hero />
      <Testimonials />
      <BrandStory />
      <BenefitsSection />
      <IngredientsSpotlight />
      <SafetyDisclaimer />
      <FinalCTA />
    </main>
  );
};

export default Home;
