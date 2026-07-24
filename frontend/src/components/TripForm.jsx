import { useState } from 'react';
import { MapPin, Navigation, Clock, Loader2 } from 'lucide-react';

export default function TripForm({ onSubmit, isLoading }) {
  const [formData, setFormData] = useState({
    current_location: 'Chicago, IL',
    pickup_location: 'Detroit, MI',
    dropoff_location: 'Cleveland, OH',
    current_cycle_used: '0.0'
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      ...formData,
      current_cycle_used: parseFloat(formData.current_cycle_used) || 0
    });
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  return (
    <div className="card">
      <h2 className="mb-4" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Navigation size={24} color="var(--primary)" />
        Plan Your Trip
      </h2>
      <form onSubmit={handleSubmit}>
        <div className="grid-2">
          <div className="form-group">
            <label htmlFor="current_location">Current Location</label>
            <div style={{ position: 'relative' }}>
              <MapPin size={18} style={{ position: 'absolute', left: '12px', top: '14px', color: 'var(--text-secondary)' }} />
              <input
                type="text"
                id="current_location"
                name="current_location"
                className="form-control"
                style={{ paddingLeft: '2.5rem' }}
                value={formData.current_location}
                onChange={handleChange}
                required
              />
            </div>
          </div>
          <div className="form-group">
            <label htmlFor="current_cycle_used">Current Cycle Used (Hours)</label>
            <div style={{ position: 'relative' }}>
              <Clock size={18} style={{ position: 'absolute', left: '12px', top: '14px', color: 'var(--text-secondary)' }} />
              <input
                type="number"
                id="current_cycle_used"
                name="current_cycle_used"
                className="form-control"
                style={{ paddingLeft: '2.5rem' }}
                value={formData.current_cycle_used}
                onChange={handleChange}
                min="0"
                max="70"
                step="0.1"
                required
              />
            </div>
          </div>
          <div className="form-group">
            <label htmlFor="pickup_location">Pickup Location</label>
            <div style={{ position: 'relative' }}>
              <MapPin size={18} style={{ position: 'absolute', left: '12px', top: '14px', color: 'var(--color-pickup)' }} />
              <input
                type="text"
                id="pickup_location"
                name="pickup_location"
                className="form-control"
                style={{ paddingLeft: '2.5rem' }}
                value={formData.pickup_location}
                onChange={handleChange}
                required
              />
            </div>
          </div>
          <div className="form-group">
            <label htmlFor="dropoff_location">Dropoff Location</label>
            <div style={{ position: 'relative' }}>
              <MapPin size={18} style={{ position: 'absolute', left: '12px', top: '14px', color: 'var(--color-dropoff)' }} />
              <input
                type="text"
                id="dropoff_location"
                name="dropoff_location"
                className="form-control"
                style={{ paddingLeft: '2.5rem' }}
                value={formData.dropoff_location}
                onChange={handleChange}
                required
              />
            </div>
          </div>
        </div>
        <div className="mt-4">
          <button type="submit" className="btn btn-primary" disabled={isLoading}>
            {isLoading ? (
              <><Loader2 size={18} className="mr-2" style={{ animation: 'spin 2s linear infinite', marginRight: '8px' }} /> Calculating Route...</>
            ) : (
              'Plan Trip & Generate Logs'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
