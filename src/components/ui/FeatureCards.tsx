import React from 'react';
import { Clock, MapPin, Shield, Brain, Network, Lock, BarChart, Zap } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './Card';

const FeatureCards: React.FC = () => {
  const features = [
    {
      icon: Clock,
      title: "Real-time Prediction",
      description: "AI-powered analysis predicts likely cash-out locations within 90 minutes of complaint submission.",
      color: "text-blue-600",
      bgColor: "bg-blue-100"
    },
    {
      icon: MapPin,
      title: "Digital Cordon",
      description: "Geofenced areas with NPCI integration to flag suspicious transactions in real-time.",
      color: "text-green-600",
      bgColor: "bg-green-100"
    },
    {
      icon: Shield,
      title: "Privacy First",
      description: "Zero PII storage with DPDP Act 2023 compliance. All data anonymized for citizen protection.",
      color: "text-purple-600",
      bgColor: "bg-purple-100"
    },
    {
      icon: Brain,
      title: "Advanced AI Models",
      description: "CST-Transformer, Federated Causal Graph, and Behavioral Digital Twin for sophisticated analysis.",
      color: "text-orange-600",
      bgColor: "bg-orange-100"
    },
    {
      icon: Network,
      title: "Multi-Agency Integration",
      description: "Seamless integration with NCRP, CFCFRMS, I4C, and banking systems for coordinated response.",
      color: "text-indigo-600",
      bgColor: "bg-indigo-100"
    },
    {
      icon: BarChart,
      title: "Advanced Analytics",
      description: "Comprehensive dashboard with real-time insights, pattern recognition, and predictive analytics.",
      color: "text-pink-600",
      bgColor: "bg-pink-100"
    }
  ];

  return (
    <div className="py-16 bg-white">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            Advanced Capabilities
          </h2>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Project AEGIS combines cutting-edge AI technologies with privacy-preserving design
            to create the most advanced cybercrime response system in India.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <Card
              key={index}
              className="group hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border-gray-200 overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-transparent via-transparent to-orange-50/50 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

              <CardHeader className="relative">
                <div className={`${feature.bgColor} w-16 h-16 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                  <feature.icon className={`h-8 w-8 ${feature.color}`} />
                </div>
                <CardTitle className="text-xl group-hover:text-orange-600 transition-colors duration-300">
                  {feature.title}
                </CardTitle>
              </CardHeader>

              <CardContent className="relative">
                <CardDescription className="text-gray-600 leading-relaxed">
                  {feature.description}
                </CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Additional highlight section */}
        <div className="mt-16 bg-gradient-to-r from-orange-50 to-blue-50 rounded-2xl p-8 border border-orange-100">
          <div className="flex items-center justify-between flex-wrap gap-8">
            <div className="flex-1 min-w-[300px]">
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                State-of-the-Art Technology Stack
              </h3>
              <p className="text-gray-600 leading-relaxed">
                Built with modern technologies including FastAPI, PostgreSQL with PostGIS, Apache Kafka,
                PyTorch, and Next.js. Our system processes millions of data points while maintaining
                sub-second response times.
              </p>
            </div>

            <div className="flex gap-4">
              <div className="text-center">
                <div className="flex items-center justify-center w-12 h-12 bg-white rounded-lg shadow-sm mb-2">
                  <Zap className="h-6 w-6 text-orange-600" />
                </div>
                <div className="text-sm font-medium text-gray-700">Lightning Fast</div>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center w-12 h-12 bg-white rounded-lg shadow-sm mb-2">
                  <Lock className="h-6 w-6 text-green-600" />
                </div>
                <div className="text-sm font-medium text-gray-700">Secure by Design</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FeatureCards;