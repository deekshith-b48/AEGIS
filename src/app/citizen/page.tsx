'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { MapPin, AlertTriangle, Shield, CheckCircle, Loader2, Navigation } from 'lucide-react';
import { submitComplaint } from '@/lib/api';
import { ComplaintData } from '@/types';

// Form validation schema
const complaintSchema = z.object({
  scam_type: z.enum(['UPI_PHISHING', 'FAKE_LOAN_APP', 'IMPERSONATION', 'LOTTERY_SCAM', 'INVESTMENT_FRAUD']),
  amount: z.number().min(101, 'Amount must be greater than ₹100').max(10000000, 'Amount cannot exceed ₹1,00,00,000'),
  victim_location: z.object({
    lat: z.number().min(-90).max(90),
    lon: z.number().min(-180).max(180),
  }),
});

type ComplaintFormData = z.infer<typeof complaintSchema>;

const scamTypes = [
  { value: 'UPI_PHISHING', label: 'UPI Phishing', description: 'Fake UPI payment requests and QR codes' },
  { value: 'FAKE_LOAN_APP', label: 'Fake Loan App', description: 'Illegal loan apps with high interest rates' },
  { value: 'IMPERSONATION', label: 'Impersonation', description: 'Someone pretending to be authority or known person' },
  { value: 'LOTTERY_SCAM', label: 'Lottery Scam', description: 'Fake lottery winnings and prize claims' },
  { value: 'INVESTMENT_FRAUD', label: 'Investment Fraud', description: 'Fake investment opportunities and schemes' },
];

export default function CitizenPortal() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDetectingLocation, setIsDetectingLocation] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState<{ lat: number; lon: number } | null>(null);
  const [submissionResult, setSubmissionResult] = useState<{ success: boolean; complaintId?: string; message?: string } | null>(null);
  const [locationTab, setLocationTab] = useState<'auto' | 'manual'>('auto');

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm<ComplaintFormData>({
    resolver: zodResolver(complaintSchema),
    defaultValues: {
      scam_type: 'UPI_PHISHING',
      amount: undefined,
      victim_location: { lat: 28.6139, lon: 77.2090 }, // Default to Delhi
    },
  });

  const detectLocation = () => {
    setIsDetectingLocation(true);
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          const location = { lat: latitude, lon: longitude };
          setSelectedLocation(location);
          setValue('victim_location', location);
          setIsDetectingLocation(false);
        },
        (error) => {
          console.error('Geolocation error:', error);
          setIsDetectingLocation(false);
          alert('Unable to detect your location. Please use the manual map selection.');
        }
      );
    } else {
      setIsDetectingLocation(false);
      alert('Geolocation is not supported by your browser. Please use manual map selection.');
    }
  };

  const onSubmit = async (data: ComplaintFormData) => {
    setIsSubmitting(true);
    try {
      const result = await submitComplaint(data);
      setSubmissionResult({
        success: true,
        complaintId: result.complaint_id,
        message: result.message,
      });
    } catch (error) {
      console.error('Submission error:', error);
      setSubmissionResult({
        success: false,
        message: 'Failed to submit complaint. Please try again.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setSubmissionResult(null);
    setSelectedLocation(null);
    setValue('victim_location', { lat: 28.6139, lon: 77.2090 });
  };

  if (submissionResult?.success) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-green-50 border border-green-200 rounded-lg p-8 text-center">
          <CheckCircle className="h-16 w-16 text-green-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-green-900 mb-2">Complaint Submitted Successfully</h2>
          <p className="text-green-700 mb-4">{submissionResult.message}</p>
          <div className="bg-white rounded-lg p-4 mb-6">
            <p className="text-sm text-gray-600 mb-1">Reference ID:</p>
            <p className="text-lg font-mono font-bold text-gray-900">AEGIS-{submissionResult.complaintId?.slice(-8).toUpperCase()}</p>
          </div>
          <p className="text-gray-700 mb-6">
            Our system is analyzing patterns to identify potential cash-out locations.
            Law enforcement has been alerted if high-risk locations are predicted.
          </p>
          <button
            onClick={resetForm}
            className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors"
          >
            Submit Another Complaint
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <Shield className="h-12 w-12 text-orange-600 mx-auto mb-4" />
        <h1 className="text-3xl font-bold text-gray-900 mb-2">File a Scam Complaint</h1>
        <p className="text-gray-600">
          Report scam incidents anonymously. Your location helps us predict potential cash-out locations.
        </p>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="flex items-start">
          <AlertTriangle className="h-5 w-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" />
          <div className="text-sm text-blue-700">
            <p className="font-semibold mb-1">Privacy Notice</p>
            <p>
              We do not collect any personally identifiable information. Only scam type, amount, and approximate location are stored.
              All data is processed according to DPDP Act 2023 guidelines.
            </p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
        {/* Scam Type Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Type of Scam
          </label>
          <div className="grid gap-3">
            {scamTypes.map((type) => (
              <label
                key={type.value}
                className="flex items-start p-4 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
              >
                <input
                  type="radio"
                  value={type.value}
                  {...register('scam_type')}
                  className="mt-1 mr-3"
                />
                <div>
                  <div className="font-medium text-gray-900">{type.label}</div>
                  <div className="text-sm text-gray-500">{type.description}</div>
                </div>
              </label>
            ))}
          </div>
          {errors.scam_type && (
            <p className="mt-1 text-sm text-red-600">{errors.scam_type.message}</p>
          )}
        </div>

        {/* Amount Input */}
        <div>
          <label htmlFor="amount" className="block text-sm font-medium text-gray-700 mb-2">
            Amount Lost (₹)
          </label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">₹</span>
            <input
              type="number"
              id="amount"
              {...register('amount', { valueAsNumber: true })}
              placeholder="Enter amount (minimum ₹101)"
              className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
            />
          </div>
          {errors.amount && (
            <p className="mt-1 text-sm text-red-600">{errors.amount.message}</p>
          )}
        </div>

        {/* Location Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Incident Location
          </label>

          <div className="border border-gray-200 rounded-lg">
            {/* Tab Navigation */}
            <div className="flex border-b border-gray-200">
              <button
                type="button"
                onClick={() => setLocationTab('auto')}
                className={`flex-1 py-2 px-4 text-sm font-medium ${
                  locationTab === 'auto'
                    ? 'bg-orange-100 text-orange-700 border-b-2 border-orange-500'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <Navigation className="h-4 w-4 inline mr-2" />
                Auto-detect
              </button>
              <button
                type="button"
                onClick={() => setLocationTab('manual')}
                className={`flex-1 py-2 px-4 text-sm font-medium ${
                  locationTab === 'manual'
                    ? 'bg-orange-100 text-orange-700 border-b-2 border-orange-500'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <MapPin className="h-4 w-4 inline mr-2" />
                Select on Map
              </button>
            </div>

            <div className="p-4">
              {locationTab === 'auto' ? (
                <div className="text-center py-4">
                  {isDetectingLocation ? (
                    <div className="flex items-center justify-center">
                      <Loader2 className="h-6 w-6 animate-spin text-orange-600 mr-3" />
                      <span className="text-gray-600">Detecting your location...</span>
                    </div>
                  ) : selectedLocation ? (
                    <div>
                      <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-3">
                        <p className="text-sm text-green-700">
                          <MapPin className="h-4 w-4 inline mr-1" />
                          Location detected: {selectedLocation.lat.toFixed(6)}, {selectedLocation.lon.toFixed(6)}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={detectLocation}
                        className="text-orange-600 hover:text-orange-700 text-sm"
                      >
                        Detect different location
                      </button>
                    </div>
                  ) : (
                    <div>
                      <button
                        type="button"
                        onClick={detectLocation}
                        className="bg-orange-600 text-white px-6 py-2 rounded-lg hover:bg-orange-700 transition-colors"
                      >
                        <Navigation className="h-4 w-4 inline mr-2" />
                        Detect My Location
                      </button>
                      <p className="text-sm text-gray-500 mt-2">
                        We'll use your browser's location services to find your current location.
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <MapPin className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-600 mb-3">Interactive map will be available here</p>
                  <p className="text-sm text-gray-500">
                    For now, using default location (Delhi) for demonstration purposes.
                  </p>
                  <div className="bg-gray-100 rounded-lg p-3 mt-3">
                    <p className="text-sm text-gray-700">
                      Default Location: 28.6139, 77.2090 (Delhi)
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Error Display */}
        {submissionResult?.success === false && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-700">{submissionResult.message}</p>
          </div>
        )}

        {/* Submit Button */}
        <div className="text-center">
          <button
            type="submit"
            disabled={isSubmitting}
            className="bg-orange-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-orange-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center mx-auto"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin mr-2" />
                Submitting...
              </>
            ) : (
              <>
                <Shield className="h-5 w-5 mr-2" />
                Submit Complaint
              </>
            )}
          </button>
          <p className="text-sm text-gray-500 mt-2">
            Your complaint will be processed immediately and analyzed for potential threats.
          </p>
        </div>
      </form>
    </div>
  );
}