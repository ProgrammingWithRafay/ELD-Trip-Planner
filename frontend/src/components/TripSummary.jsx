export default function TripSummary({ distance, duration, days }) {
  return (
    <div className="card flex items-center justify-between" style={{ backgroundColor: 'var(--primary-light)', borderColor: 'var(--primary-light)' }}>
      <div className="text-center w-full">
        <div style={{ fontSize: '0.875rem', color: 'var(--primary)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Distance</div>
        <div style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', fontWeight: '700', color: 'var(--text-primary)' }}>
          {Math.round(distance).toLocaleString()} <span style={{ fontSize: '1rem', fontWeight: '500', color: 'var(--text-secondary)' }}>mi</span>
        </div>
      </div>
      <div style={{ width: '1px', height: '40px', backgroundColor: 'rgba(8, 145, 178, 0.2)' }}></div>
      <div className="text-center w-full">
        <div style={{ fontSize: '0.875rem', color: 'var(--primary)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Drive Time</div>
        <div style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', fontWeight: '700', color: 'var(--text-primary)' }}>
          {duration.toFixed(1)} <span style={{ fontSize: '1rem', fontWeight: '500', color: 'var(--text-secondary)' }}>hrs</span>
        </div>
      </div>
      <div style={{ width: '1px', height: '40px', backgroundColor: 'rgba(8, 145, 178, 0.2)' }}></div>
      <div className="text-center w-full">
        <div style={{ fontSize: '0.875rem', color: 'var(--primary)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Days</div>
        <div style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', fontWeight: '700', color: 'var(--text-primary)' }}>
          {days} <span style={{ fontSize: '1rem', fontWeight: '500', color: 'var(--text-secondary)' }}>days</span>
        </div>
      </div>
    </div>
  );
}
