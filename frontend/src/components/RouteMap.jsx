import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { useEffect } from 'react';

// Custom icons using Lucide-like SVG paths or simple colored dots
const createIcon = (color) => {
  return L.divIcon({
    className: 'custom-icon',
    html: `<div style="background-color: ${color}; width: 16px; height: 16px; border-radius: 50%; border: 2px solid white; box-shadow: 0 1px 3px rgba(0,0,0,0.3);"></div>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
    popupAnchor: [0, -8]
  });
};

const ICONS = {
  start: createIcon('var(--text-secondary)'),
  pickup: createIcon('var(--color-pickup)'),
  dropoff: createIcon('var(--color-dropoff)'),
  fuel: createIcon('var(--color-rest)'),
  rest: createIcon('var(--color-rest)')
};

// Component to automatically adjust map bounds to fit route
function MapBounds({ routeGeometry }) {
  const map = useMap();
  useEffect(() => {
    if (routeGeometry && routeGeometry.length > 0) {
      const bounds = L.latLngBounds(routeGeometry);
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [map, routeGeometry]);
  return null;
}

export default function RouteMap({ routeGeometry, stops }) {
  if (!routeGeometry || routeGeometry.length === 0) {
    return (
      <div className="card flex items-center" style={{ height: '400px', justifyContent: 'center', backgroundColor: '#f1f5f9', color: 'var(--text-secondary)' }}>
        Submit a trip plan to see the route map.
      </div>
    );
  }

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <MapContainer 
        center={routeGeometry[0]} 
        zoom={5} 
        scrollWheelZoom={true} 
        style={{ height: '400px', width: '100%', zIndex: 1 }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Polyline positions={routeGeometry} color="var(--primary)" weight={4} opacity={0.8} />
        
        {stops && stops.map((stop, idx) => (
          <Marker 
            key={`${stop.type}-${idx}`} 
            position={[stop.lat, stop.lng]} 
            icon={ICONS[stop.type] || ICONS.start}
          >
            <Popup>
              <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>{stop.type}</div>
              <div>{stop.location_label}</div>
              {stop.day && <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Day {stop.day}</div>}
            </Popup>
          </Marker>
        ))}

        <MapBounds routeGeometry={routeGeometry} />
      </MapContainer>
    </div>
  );
}
