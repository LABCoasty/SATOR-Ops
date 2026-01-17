import { HeroSection } from "@/components/landing/hero-section"
import { ProblemSection } from "@/components/landing/problem-section"
import { BenefitsSection } from "@/components/landing/benefits-section"
import { IndustriesSection } from "@/components/landing/industries-section"
import { TrustLayerSection } from "@/components/landing/trust-layer-section"
import { LandingNav } from "@/components/landing/landing-nav"
import { LandingFooter } from "@/components/landing/landing-footer"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <LandingNav />
      <main>
        <HeroSection />
        <ProblemSection />
        <BenefitsSection />
        <IndustriesSection />
        <TrustLayerSection />
      </main>
      <LandingFooter />
    </div>
  )
}
