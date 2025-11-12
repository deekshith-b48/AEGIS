import HeroSection from "@/components/ui/HeroSection";
import FeatureCards from "@/components/ui/FeatureCards";
import ProcessFlow from "@/components/ui/ProcessFlow";
import { Badge } from "@/components/ui/Badge";

export default function Home() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <HeroSection />

      {/* Advanced Features */}
      <FeatureCards />

      {/* Process Flow */}
      <ProcessFlow />

      {/* Compliance Notice */}
      <div className="py-16 bg-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-gradient-to-r from-blue-50 to-orange-50 rounded-2xl p-8 border border-blue-100">
            <div className="text-center">
              <div className="flex justify-center mb-4">
                <Badge variant="secondary" className="text-sm">
                  🏆 SIH 2025 Finals
                </Badge>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                MVP Demonstration Prototype
              </h3>
              <p className="text-gray-700 leading-relaxed max-w-2xl mx-auto">
                This is an advanced prototype demonstrating the capabilities of Project AEGIS for the Smart India Hackathon 2025 Finals.
                The system showcases a complete cybercrime response platform with simulated integrations and mock data.
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-3">
                <Badge variant="outline">No Real Banking APIs</Badge>
                <Badge variant="outline">Zero Personal Data</Badge>
                <Badge variant="outline">Mock Integrations</Badge>
                <Badge variant="outline">Demo Environment</Badge>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}