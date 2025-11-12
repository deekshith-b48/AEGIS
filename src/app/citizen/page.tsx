/**
 * Project AEGIS Greenfield Citizen Complaint Portal
 * Exact implementation with greenfield API integration
 * Interactive MapLibre GL map for location selection
 * Zero PII design with privacy compliance
 */

'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Map, { MapRef, NavigationControl, ScaleControl, Marker } from 'react-map-gl/maplibre';
import { MapPin, AlertTriangle, Shield, CheckCircle, Loader2, Navigation, X, Phone, DollarSign } from 'lucide-react';
import { submitComplaint } from '@/lib/greenfield_api';
import { GreenfieldComplaintRequest, GreenfieldComplaintResponse } from '@/lib/greenfield_api';

// Form validation schema
const complaintSchema = z.object({
  fraud_type: z.enum(['UPI_PHISHING', 'FAKE_LOAN_APP', 'IMPERSONATION', 'LOTTERY_SCAM', 'INVESTMENT_FRAUD']),
  amount: z.number().min(101, 'Amount must be greater than ₹100').max(10000000, 'Amount cannot exceed ₹1,00,00,000'),
  victim_lat: z.number().min(-90).max(90),
  victim_lon: z.number().min(-180).max(180),
});

type ComplaintFormData = z.infer<typeof complaintSchema>;

const scamTypes = [
  {
    value: 'UPI_PHISHING',
    label: 'UPI Phishing',
    description: 'Fake UPI payment requests, QR codes, or payment links',
    icon: <Phone className="h-5 w-5" />
  },
  {
    value: 'FAKE_LOAN_APP',
    label: 'Fake Loan App',
    description: 'Illegal loan apps with excessive interest rates or processing fees',
    icon: <DollarSign className="h-5 w-5" />
  },
  {
    value: 'IMPERSONATION',
    label: 'Impersonation',
    description: 'Someone pretending to be authority, government official, or known person',
    icon: <Shield className="h-5 w-5" />
  },
  {
    value: 'LOTTERY_SCAM',
    label: 'Lottery Scam',
    description: 'Fake lottery winnings, prize claims, or inheritance notifications',
    icon: <AlertTriangle className="h-5 w-5" />
  },
  {
    value: 'INVESTMENT_FRAUD',
    label: 'Investment Fraud',
    description: 'Fake investment opportunities, Ponzi schemes, or high-return promises',
    icon: <DollarSign className="h-5 w-5" />
  },
];

export default function CitizenPortal() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDetectingLocation, setIsDetectingLocation] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState<{ lat: number; lon: number } | null>(null);
  const [submissionResult, setSubmissionResult] = useState<GreenfieldComplaintResponse | null>(null);
  const [locationTab, setLocationTab] = useState<'auto' | 'manual'>('auto');
  const [mapLocation, setMapLocation] = useState<{ lat: number; lon: number }>({ lat: 28.6139, lon: 77.2090 });
  const [showSuccessAnimation, setShowSuccessAnimation] = useState(false);
  const mapRef = useRef<MapRef>(null);

  // MapLibre GL configuration with open tiles
  const MAP_STYLE = 'https://tiles.stadiamaps.com/styles/osm_bright/style.json';

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
    reset,
  } = useForm<ComplaintFormData>({
    resolver: zodResolver(complaintSchema),
    defaultValues: {
      fraud_type: 'UPI_PHISHING',
      amount: undefined,
      victim_lat: 28.6139,
      victim_lon: 77.2090,
    },
  });

  // Detect user's location
  const detectLocation = () => {
    setIsDetectingLocation(true);
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          const location = { lat: latitude, lon: longitude };
          setSelectedLocation(location);
          setMapLocation(location);
          setValue('victim_lat', latitude);
          setValue('victim_lon', longitude);
          setIsDetectingLocation(false);
        },
        (error) => {
          console.error('Geolocation error:', error);
          setIsDetectingLocation(false);
          alert('Unable to detect your location. Please use manual selection.');
        }
      );
    } else {
      setIsDetectingLocation(false);
      alert('Geolocation is not supported by your browser.');
    }
  };

  // Handle map click for manual location selection
  const handleMapClick = (event: any) => {
    const { lng, lat } = event.lngLat;
    const location = { lat, lon: lng };
    setSelectedLocation(location);
    setMapLocation(location);
    setValue('victim_lat', lat);
    setValue('victim_lon', lng);
  };

  // Handle marker drag for manual location selection
  const handleMarkerDrag = (event: any) => {
    const { lng, lat } = event.lngLat;
    const location = { lat, lon: lng };
    setSelectedLocation(location);
    setValue('victim_lat', lat);
    setValue('victim_lon', lng);
  };

  // Form submission
  const onSubmit = async (data: ComplaintFormData) => {
    setIsSubmitting(true);
    try {
      const result = await submitComplaint(data);
      setSubmissionResult(result);
      setShowSuccessAnimation(true);

      // Trigger success animation
      setTimeout(() => setShowSuccessAnimation(false), 2000);

    } catch (error) {
      console.error('Submission error:', error);
      setSubmissionResult({
        success: false,
        complaint_id: '',
        message: 'Failed to submit complaint. Please try again.',
        prediction_triggered: false
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Reset form
  const resetForm = () => {
    setSubmissionResult(null);
    setSelectedLocation(null);
    setShowSuccessAnimation(false);
    reset();
    setMapLocation({ lat: 28.6139, lon: 77.2090 });
  };

  // Success view
  if (submissionResult?.success) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className={`bg-green-50 border border-green-200 rounded-lg p-8 text-center ${showSuccessAnimation ? 'animate-pulse' : ''}`}>
          <div className="flex justify-center mb-6">
            <div className={`bg-green-100 rounded-full p-6 ${showSuccessAnimation ? 'animate-bounce' : ''}`}>
              <CheckCircle className="h-16 w-16 text-green-600" />
            </div>
          </div>
          <h2 className="text-3xl font-bold text-green-900 mb-4">Complaint Submitted Successfully</h2>
          <p className="text-green-700 mb-6 text-lg">{submissionResult.message}</p>

          {submissionResult.prediction_triggered && (
            <div className="bg-white rounded-lg p-6 mb-6 border border-green-300">
              <div className="flex items-center justify-center mb-3">
                <AlertTriangle className="h-6 w-6 text-orange-600 mr-2" />
                <span className="text-orange-600 font-semibold">High-Confidence Prediction Triggered</span>
              </div>
              <p className="text-gray-700">
                Our AI engine has identified potential high-risk locations. Law enforcement has been alerted.
              </p>
            </div>
          )}

          <div className="bg-white rounded-lg p-4 mb-6 border border-gray-200">
            <p className="text-sm text-gray-600 mb-1">Reference ID (save for your records):</p>
            <p className="text-lg font-mono font-bold text-gray-900 bg-gray-100 px-3 py-2 rounded">
              AEGIS-{submissionResult.complaint_id?.slice(-8).toUpperCase()}
            </p>
          </div>

          <div className="bg-blue-50 rounded-lg p-4 mb-6 border border-blue-200">
            <p className="text-sm text-blue-700">
              <strong>Privacy Notice:</strong> No personal information has been stored. Only anonymous location and transaction details are used for threat analysis.
            </p>
          </div>

          <button
            onClick={resetForm}
            className="bg-green-600 text-white px-8 py-3 rounded-lg hover:bg-green-700 transition-colors font-semibold flex items-center mx-auto"
          >
            <Shield className="h-5 w-5 mr-2" />
            Submit Another Complaint
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="flex justify-center items-center mb-6">
          <Shield className="h-12 w-12 text-orange-600 mr-4" />
          <h1 className="text-4xl font-bold text-gray-900">File a Scam Complaint</h1>
        </div>
        <p className="text-lg text-gray-600 max-w-3xl mx-auto mb-4">
          Report scam incidents anonymously. Your location helps us predict potential cash-out locations and enable proactive intervention.
        </p>
        <p className="text-sm text-gray-500">
          All data is processed according to DPDP Act 2023 guidelines with zero PII storage.
        </p>
      </div>

      {/* Privacy Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
        <div className="flex items-start">
          <Shield className="h-6 w-6 text-blue-600 mt-1 mr-3 flex-shrink-0" />
          <div className="text-sm text-blue-700">
            <p className="font-semibold mb-2">🔒 Privacy-First Reporting</p>
            <p>
              We collect <strong>zero personally identifiable information</strong>. Only scam type, amount range, and approximate location are stored.
              Your identity remains completely anonymous throughout the process. Location data is limited to coordinates only.
            </p>
          </div>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
        {/* Scam Type Selection */}
        <div>
          <label className="block text-lg font-medium text-gray-700 mb-4">
            Type of Scam
          </label>
          <div className="grid gap-4">
            {scamTypes.map((type) => (
              <label
                key={type.value}
                className="flex items-start p-4 border-2 border-gray-200 rounded-lg cursor-pointer hover:border-orange-300 hover:bg-orange-50 transition-all"
              >
                <input
                  type="radio"
                  value={type.value}
                  {...register('fraud_type')}
                  className="mt-1 mr-4 text-orange-600"
                />
                <div className="flex-1">
                  <div className="flex items-center font-medium text-gray-900 mb-1">
                    {type.icon}
                    <span className="ml-2">{type.label}</span>
                  </div>
                  <p className="text-sm text-gray-600">{type.description}</p>
                </div>
              </label>
            ))}
          </div>
          {errors.fraud_type && (
            <p className="mt-2 text-sm text-red-600">{errors.fraud_type.message}</p>
          )}
        </div>

        {/* Amount Input */}
        <div>
          <label htmlFor="amount" className="block text-lg font-medium text-gray-700 mb-2">
            Amount Lost (₹)
          </label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 text-lg">₹</span>
            <input
              type="number"
              id="amount"
              {...register('amount', { valueAsNumber: true })}
              placeholder="Enter amount (minimum ₹101)"
              className="w-full pl-8 pr-3 py-3 text-lg border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
            />
          </div>
          {errors.amount && (
            <p className="mt-1 text-sm text-red-600">{errors.amount.message}</p>
          )}
        </div>

        {/* Location Selection */}
        <div>
          <label className="block text-lg font-medium text-gray-700 mb-4">
            Incident Location
          </label>

          <div className="border-2 border-gray-200 rounded-lg overflow-hidden">
            {/* Tab Navigation */}
            <div className="flex border-b border-gray-200 bg-gray-50">
              <button
                type="button"
                onClick={() => setLocationTab('auto')}
                className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
                  locationTab === 'auto'
                    ? 'bg-orange-100 text-orange-700 border-b-2 border-orange-500'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
                }`}
              >
                <Navigation className="h-4 w-4 inline mr-2" />
                Auto-Detect Location
              </button>
              <button
                type="button"
                onClick={() => setLocationTab('manual')}
                className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
                  locationTab === 'manual'
                    ? 'bg-orange-100 text-orange-700 border-b-2 border-orange-500'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
                }`}
              >
                <MapPin className="h-4 w-4 inline mr-2" />
                Select on Map
              </button>
            </div>

            <div className="p-4">
              {locationTab === 'auto' ? (
                <div className="text-center py-8">
                  {isDetectingLocation ? (
                    <div className="flex items-center justify-center">
                      <Loader2 className="h-8 w-8 animate-spin text-orange-600 mr-3" />
                      <span className="text-lg text-gray-600">Detecting your location...</span>
                    </div>
                  ) : selectedLocation ? (
                    <div>
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                        <div className="flex items-center">
                          <MapPin className="h-5 w-5 text-green-600 mr-2" />
                          <p className="text-green-700">
                            Location detected: {selectedLocation.lat.toFixed(6)}, {selectedLocation.lon.toFixed(6)}
                          </p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={detectLocation}
                        className="text-orange-600 hover:text-orange-700 text-sm font-medium"
                      >
                        Detect different location
                      </button>
                    </div>
                  ) : (
                    <div>
                      <button
                        type="button"
                        onClick={detectLocation}
                        className="bg-orange-600 text-white px-6 py-3 rounded-lg hover:bg-orange-700 transition-colors font-medium"
                      >
                        <Navigation className="h-5 w-5 inline mr-2" />
                        Detect My Location
                      </button>
                      <p className="text-sm text-gray-500 mt-3">
                        We'll use your browser's location services to find your current location.
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  <p className="text-sm text-gray-600 mb-4">
                    Click on the map or drag the marker to select the incident location
                  </p>
                  <div className="h-96 rounded-lg overflow-hidden border-2 border-gray-300">
                    <Map
                      ref={mapRef}
                      mapLibreImport="maplibre-gl"
                      mapStyle={MAP_STYLE}
                      initialViewState={{
                        longitude: mapLocation.lon,
                        latitude: mapLocation.lat,
                        zoom: 13,
                      }}
                      onClick={handleMapClick}
                      style={{ width: '100%', height: '100%' }}
                    >
                      <NavigationControl position="top-right" />
                      <ScaleControl />

                      {selectedLocation && (
                        <Marker
                          longitude={selectedLocation.lon}
                          latitude={selectedLocation.lat}
                          draggable
                          onDragEnd={handleMarkerDrag}
                        >
                          <div className="bg-red-600 text-white p-2 rounded-full shadow-lg">
                            <MapPin className="h-6 w-6" />
                          </div>
                        </Marker>
                      )}
                    </Map>
                  </div>
                  {selectedLocation && (
                    <div className="mt-3 text-sm text-gray-600 bg-gray-50 p-2 rounded">
                      Selected: {selectedLocation.lat.toFixed(6)}, {selectedLocation.lon.toFixed(6)}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Error Display */}
        {submissionResult?.success === false && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <XCircle className="h-5 w-5 text-red-600 mr-2" />
              <p className="text-red-700">{submissionResult.message}</p>
            </div>
          </div>
        )}

        {/* Submit Button */}
        <div className="text-center pt-6">
          <button
            type="submit"
            disabled={isSubmitting || !selectedLocation}
            className="bg-orange-600 text-white px-10 py-4 rounded-lg hover:bg-orange-700 transition-colors font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center mx-auto"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-6 w-6 animate-spin mr-3" />
                Submitting Complaint...
              </>
            ) : (
              <>
                <Shield className="h-6 w-6 mr-3" />
                Submit Anonymized Complaint
              </>
            )}
          </button>
          <p className="text-sm text-gray-500 mt-3">
            Your complaint will be processed immediately and analyzed for potential threats. No personal information is stored.
          </p>
        </div>
      </form>
    </div>
  );
}