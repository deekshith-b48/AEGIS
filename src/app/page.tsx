import Link from "next/link";
import { Shield, AlertTriangle, MapPin, Clock, Users, BarChart } from "lucide-react";

export default function Home() {
  return (
    <div className="max-w-6xl mx-auto">
      {/* Hero Section */}
      <div className="text-center mb-16">
        <div className="flex justify-center items-center mb-6">
          <Shield className="h-16 w-16 text-orange-600 mr-4" />
          <h1 className="text-5xl font-bold text-gray-900">
            Project AEGIS
          </h1>
        </div>
        <h2 className="text-2xl text-gray-600 mb-4">
          Anticipatory Engine for Geolocated Intervention against Scams
        </h2>
        <p className="text-lg text-gray-500 max-w-3xl mx-auto mb-8">
          Transforming India's cybercrime response from reactive reporting to anticipatory disruption.
          Our AI-powered system predicts high-risk cash withdrawal locations within 90 minutes of scam complaints.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/citizen"
            className="bg-orange-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-orange-700 transition-colors flex items-center justify-center"
          >
            <AlertTriangle className="h-5 w-5 mr-2" />
            File a Complaint
          </Link>
          <Link
            href="/lea"
            className="bg-green-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors flex items-center justify-center"
          >
            <MapPin className="h-5 w-5 mr-2" />
            LEA Dashboard
          </Link>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid md:grid-cols-3 gap-8 mb-16">
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <div className="flex items-center mb-4">
            <Clock className="h-8 w-8 text-blue-600 mr-3" />
            <h3 className="text-xl font-semibold text-gray-900">Real-time Prediction</h3>
          </div>
          <p className="text-gray-600">
            AI-powered analysis predicts likely cash-out locations within 90 minutes of complaint submission.
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <div className="flex items-center mb-4">
            <MapPin className="h-8 w-8 text-green-600 mr-3" />
            <h3 className="text-xl font-semibold text-gray-900">Digital Cordon</h3>
          </div>
          <p className="text-gray-600">
            Geofenced areas with simulated NPCI integration to flag suspicious transactions in real-time.
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <div className="flex items-center mb-4">
            <Shield className="h-8 w-8 text-purple-600 mr-3" />
            <h3 className="text-xl font-semibold text-gray-900">Privacy First</h3>
          </div>
          <p className="text-gray-600">
            Zero PII storage with DPDP Act 2023 compliance. All data anonymized for citizen protection.
          </p>
        </div>
      </div>

      {/* Statistics Section */}
      <div className="bg-gray-100 rounded-lg p-8 mb-16">
        <h3 className="text-2xl font-bold text-center text-gray-900 mb-8">System Performance</h3>
        <div className="grid md:grid-cols-4 gap-6 text-center">
          <div>
            <div className="text-3xl font-bold text-orange-600 mb-2">
              <BarChart className="h-8 w-8 mx-auto mb-2" />
              58%
            </div>
            <p className="text-gray-600">System Accuracy</p>
          </div>
          <div>
            <div className="text-3xl font-bold text-blue-600 mb-2">
              <Clock className="h-8 w-8 mx-auto mb-2" />
              &lt;2s
            </div>
            <p className="text-gray-600">Complaint Processing</p>
          </div>
          <div>
            <div className="text-3xl font-bold text-green-600 mb-2">
              <MapPin className="h-8 w-8 mx-auto mb-2" />
              90min
            </div>
            <p className="text-gray-600">Prediction Window</p>
          </div>
          <div>
            <div className="text-3xl font-bold text-purple-600 mb-2">
              <Users className="h-8 w-8 mx-auto mb-2" />
              0
            </div>
            <p className="text-gray-600">PII Stored</p>
          </div>
        </div>
      </div>

      {/* How It Works */}
      <div className="mb-16">
        <h3 className="text-2xl font-bold text-center text-gray-900 mb-8">How It Works</h3>
        <div className="grid md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="bg-orange-100 rounded-full p-6 w-24 h-24 mx-auto mb-4 flex items-center justify-center">
              <span className="text-2xl font-bold text-orange-600">1</span>
            </div>
            <h4 className="text-lg font-semibold mb-2">Citizen Reports</h4>
            <p className="text-gray-600">
              Victims file anonymous complaints with scam type, amount, and location.
            </p>
          </div>
          <div className="text-center">
            <div className="bg-blue-100 rounded-full p-6 w-24 h-24 mx-auto mb-4 flex items-center justify-center">
              <span className="text-2xl font-bold text-blue-600">2</span>
            </div>
            <h4 className="text-lg font-semibold mb-2">AI Analysis</h4>
            <p className="text-gray-600">
              Rule-based engine predicts top 3 likely cash-out locations with confidence scores.
            </p>
          </div>
          <div className="text-center">
            <div className="bg-green-100 rounded-full p-6 w-24 h-24 mx-auto mb-4 flex items-center justify-center">
              <span className="text-2xl font-bold text-green-600">3</span>
            </div>
            <h4 className="text-lg font-semibold mb-2">LEA Action</h4>
            <p className="text-gray-600">
              Law enforcement receives real-time alerts and can activate digital cordons.
            </p>
          </div>
        </div>
      </div>

      {/* Compliance Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
        <h4 className="text-lg font-semibold text-blue-900 mb-2">MVP Demonstration</h4>
        <p className="text-blue-700">
          This is a prototype for SIH 2025 Finals. Features use mock integrations and simulated data.
          No real banking APIs or personal data are processed.
        </p>
      </div>
    </div>
  );
}