import React from 'react';
import Link from 'next/link';
import { Shield, AlertTriangle, MapPin, ArrowRight, Zap, ShieldCheck, Lock } from 'lucide-react';
import { Button } from './Button';
import { Badge } from './Badge';

const HeroSection: React.FC = () => {
  const features = [
    { icon: Zap, text: "90-min Prediction", color: "text-blue-600" },
    { icon: ShieldCheck, text: "AI-Powered", color: "text-green-600" },
    { icon: Lock, text: "Zero PII Storage", color: "text-purple-600" }
  ];

  return (
    <div className="relative overflow-hidden bg-gradient-to-br from-orange-50 via-white to-blue-50">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-grid-black/[0.02] bg-[size:60px_60px]" />
      <div className="absolute right-0 top-0 -z-10 h-[600px] w-[600px] rounded-full bg-orange-200/20 blur-3xl" />
      <div className="absolute left-0 bottom-0 -z-10 h-[400px] w-[400px] rounded-full bg-blue-200/20 blur-3xl" />

      <div className="relative mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8 lg:py-32">
        <div className="text-center">
          {/* Badge */}
          <div className="flex justify-center mb-6">
            <Badge variant="secondary" className="animate-fade-in">
              🇮🇳 SIH 2025 Finals • Transforming Cybercrime Response
            </Badge>
          </div>

          {/* Main heading */}
          <div className="flex justify-center items-center mb-8 animate-slide-up">
            <div className="relative">
              <div className="absolute inset-0 bg-orange-600/20 blur-3xl transform scale-110 animate-pulse" />
              <Shield className="relative h-20 w-20 text-orange-600 mr-6 drop-shadow-lg" />
            </div>
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold bg-gradient-to-r from-orange-600 to-orange-800 bg-clip-text text-transparent leading-tight">
              Project AEGIS
            </h1>
          </div>

          {/* Subtitle */}
          <h2 className="text-2xl sm:text-3xl text-gray-600 mb-6 animate-slide-up-delay-1 max-w-4xl mx-auto leading-relaxed">
            Anticipatory Engine for Geolocated Intervention against Scams
          </h2>

          {/* Description */}
          <p className="text-lg text-gray-500 max-w-3xl mx-auto mb-8 animate-slide-up-delay-2 leading-relaxed">
            Transforming India's cybercrime response from reactive reporting to anticipatory disruption.
            Our advanced AI system predicts high-risk cash withdrawal locations within 90 minutes of scam complaints.
          </p>

          {/* Feature pills */}
          <div className="flex flex-wrap justify-center gap-4 mb-10 animate-slide-up-delay-3">
            {features.map((feature, index) => (
              <div key={index} className="flex items-center space-x-2 bg-white/80 backdrop-blur-sm px-4 py-2 rounded-full border border-gray-200 shadow-sm hover:shadow-md transition-all duration-200">
                <feature.icon className={`h-4 w-4 ${feature.color}`} />
                <span className="text-sm font-medium text-gray-700">{feature.text}</span>
              </div>
            ))}
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16 animate-slide-up-delay-4">
            <Link href="/citizen">
              <Button size="lg" className="group text-lg px-8 py-4 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200">
                <AlertTriangle className="h-5 w-5 mr-2 group-hover:animate-pulse" />
                File a Complaint
                <ArrowRight className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <Link href="/lea">
              <Button variant="outline" size="lg" className="group text-lg px-8 py-4 border-2 hover:bg-gray-50 transform hover:-translate-y-0.5 transition-all duration-200">
                <MapPin className="h-5 w-5 mr-2" />
                LEA Dashboard
                <ArrowRight className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
          </div>

          {/* Stats preview */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 animate-fade-in-delay-5">
            <div className="text-center p-4 bg-white/60 backdrop-blur-sm rounded-xl border border-gray-200/50">
              <div className="text-3xl font-bold text-orange-600 mb-1">58%</div>
              <div className="text-sm text-gray-600">System Accuracy</div>
            </div>
            <div className="text-center p-4 bg-white/60 backdrop-blur-sm rounded-xl border border-gray-200/50">
              <div className="text-3xl font-bold text-blue-600 mb-1">&lt;2s</div>
              <div className="text-sm text-gray-600">Processing Time</div>
            </div>
            <div className="text-center p-4 bg-white/60 backdrop-blur-sm rounded-xl border border-gray-200/50">
              <div className="text-3xl font-bold text-green-600 mb-1">90min</div>
              <div className="text-sm text-gray-600">Prediction Window</div>
            </div>
            <div className="text-center p-4 bg-white/60 backdrop-blur-sm rounded-xl border border-gray-200/50">
              <div className="text-3xl font-bold text-purple-600 mb-1">0</div>
              <div className="text-sm text-gray-600">PII Stored</div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom wave decoration */}
      <div className="absolute bottom-0 left-0 right-0">
        <svg className="w-full h-12 text-gray-50" viewBox="0 0 1440 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M0 48L60 40C120 32 240 16 360 13.3C480 11 600 21 720 26.7C840 32 960 32 1080 29.3C1200 27 1320 21 1380 18.7L1440 16V48H1380C1320 48 1200 48 1080 48C960 48 840 48 720 48C600 48 480 48 360 48C240 48 120 48 60 48H0Z" fill="currentColor"/>
        </svg>
      </div>
    </div>
  );
};

export default HeroSection;