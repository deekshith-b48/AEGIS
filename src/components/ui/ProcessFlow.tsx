import React from 'react';
import { User, Brain, MapPin, Shield, ArrowRight } from 'lucide-react';

const ProcessFlow: React.FC = () => {
  const steps = [
    {
      icon: User,
      title: "Citizen Reports",
      description: "Victims file anonymous complaints with scam type, amount, and location through secure channels.",
      color: "orange",
      bgColor: "bg-orange-100",
      textColor: "text-orange-600"
    },
    {
      icon: Brain,
      title: "AI Analysis",
      description: "Advanced AI models analyze patterns, predict locations, and calculate confidence scores in real-time.",
      color: "blue",
      bgColor: "bg-blue-100",
      textColor: "text-blue-600"
    },
    {
      icon: MapPin,
      title: "Predictive Mapping",
      description: "System generates top 3 likely cash-out locations with 90-minute prediction windows and risk scores.",
      color: "green",
      bgColor: "bg-green-100",
      textColor: "text-green-600"
    },
    {
      icon: Shield,
      title: "LEA Action",
      description: "Law enforcement receives real-time alerts and can activate digital cordons for immediate intervention.",
      color: "purple",
      bgColor: "bg-purple-100",
      textColor: "text-purple-600"
    }
  ];

  return (
    <div className="py-16 bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            How It Works
          </h2>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Our streamlined process transforms citizen complaints into actionable intelligence
            within seconds, enabling rapid response to cybercrime threats.
          </p>
        </div>

        <div className="relative">
          {/* Connection line */}
          <div className="hidden lg:block absolute top-1/2 left-0 right-0 h-0.5 bg-gradient-to-r from-orange-200 via-blue-200 to-purple-200 -translate-y-1/2 z-0" />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {steps.map((step, index) => (
              <div key={index} className="relative group">
                {/* Step number */}
                <div className="absolute -top-2 -right-2 w-8 h-8 bg-white rounded-full shadow-md flex items-center justify-center text-sm font-bold text-gray-700 border-2 border-gray-200 z-10">
                  {index + 1}
                </div>

                {/* Arrow connector for mobile */}
                {index < steps.length - 1 && (
                  <div className="lg:hidden flex justify-center my-4">
                    <ArrowRight className="h-5 w-5 text-gray-400" />
                  </div>
                )}

                {/* Step card */}
                <div className="relative bg-white rounded-xl p-6 shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border border-gray-100">
                  {/* Icon */}
                  <div className={`${step.bgColor} w-16 h-16 rounded-xl flex items-center justify-center mb-4 mx-auto group-hover:scale-110 transition-transform duration-300`}>
                    <step.icon className={`h-8 w-8 ${step.textColor}`} />
                  </div>

                  {/* Content */}
                  <div className="text-center">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-orange-600 transition-colors duration-300">
                      {step.title}
                    </h3>
                    <p className="text-sm text-gray-600 leading-relaxed">
                      {step.description}
                    </p>
                  </div>

                  {/* Hover effect background */}
                  <div className={`absolute inset-0 bg-gradient-to-br from-${step.color}-50/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-xl pointer-events-none`} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Additional info */}
        <div className="mt-16 grid md:grid-cols-2 gap-8">
          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">⚡ Lightning Fast Processing</h3>
            <p className="text-gray-600 leading-relaxed mb-4">
              From complaint submission to actionable intelligence in under 2 seconds. Our
              optimized data pipeline ensures real-time response capabilities.
            </p>
            <div className="flex items-center text-sm text-gray-500">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse" />
              System Operational
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">🔒 Privacy by Design</h3>
            <p className="text-gray-600 leading-relaxed mb-4">
              All citizen data is anonymized using advanced cryptographic techniques. Zero
              PII storage ensures complete compliance with DPDP Act 2023.
            </p>
            <div className="flex items-center text-sm text-gray-500">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse" />
              Fully Compliant
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProcessFlow;