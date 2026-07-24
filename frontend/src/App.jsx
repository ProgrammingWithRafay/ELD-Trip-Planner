import { useState } from 'react';
import TripForm from './components/TripForm';
import TripSummary from './components/TripSummary';
import RouteMap from './components/RouteMap';
import LogSheet from './components/LogSheet';

export default function App() {
  const [tripPlan, setTripPlan] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handlePlanTrip = async (formData) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('http://127.0.0.1:8000/api/plan-trip/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'An unexpected error occurred');
      }
      
      setTripPlan(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container">
      <header className="mb-8 text-center flex flex-col items-center">
        <img src="/logo.png" alt="ELD Trip Planner Logo" style={{ height: '80px', marginBottom: '1rem', borderRadius: '12px' }} />
        <h1 style={{ fontSize: '2.5rem', color: 'var(--primary)', marginBottom: '0.5rem' }}>
          ELD Trip Planner
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          FMCSA-compliant paper log generator and routing engine
        </p>
      </header>

      {error && (
        <div className="alert alert-error">
          <strong>Error: </strong> {error}
        </div>
      )}

      {tripPlan && tripPlan.warnings && tripPlan.warnings.length > 0 && (
        <div className="alert" style={{ backgroundColor: '#FEF3C7', color: '#B45309', border: '1px solid #FDE68A' }}>
          <strong>Notice: </strong> {tripPlan.warnings[0]}
        </div>
      )}

      {/* If we have a trip plan, we wrap the form in a details/summary to save space */}
      {tripPlan ? (
        <details className="card" style={{ padding: '1rem 1.5rem', marginBottom: '1.5rem' }}>
          <summary style={{ cursor: 'pointer', fontWeight: 600, color: 'var(--primary)', outline: 'none' }}>
            Edit Trip Parameters
          </summary>
          <div className="mt-4">
            <TripForm onSubmit={handlePlanTrip} isLoading={isLoading} />
          </div>
        </details>
      ) : (
        <TripForm onSubmit={handlePlanTrip} isLoading={isLoading} />
      )}

      {tripPlan && (
        <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
          <TripSummary 
            distance={tripPlan.route.distance_miles} 
            duration={tripPlan.route.duration_hours} 
            days={tripPlan.daily_logs.length} 
          />
          
          <RouteMap routeGeometry={tripPlan.route.geometry} stops={tripPlan.stops} />
          
          <div className="mt-8 mb-4">
            <h2 style={{ fontSize: '1.75rem', borderBottom: '2px solid var(--border-color)', paddingBottom: '0.5rem' }}>
              Daily Logs
            </h2>
          </div>
          
          {tripPlan.daily_logs.map((log, idx) => (
            <LogSheet key={`day-${log.day}`} log={log} index={idx} />
          ))}
        </div>
      )}
      
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
