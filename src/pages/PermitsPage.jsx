import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const API_BASE = 'http://localhost:5000/api';

// Fix Leaflet default marker icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom marker icons by permit type
const createIcon = (color) => {
  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div style="
        background-color: ${color};
        width: 24px;
        height: 24px;
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        border: 2px solid white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
      "></div>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 24],
    popupAnchor: [0, -24],
  });
};

const permitTypeColors = {
  'Electrical Permit': '#EAB308',      // Yellow
  'Building Permit': '#3B82F6',        // Blue
  'Plumbing Permit': '#22C55E',        // Green
  'Gas Permit': '#F97316',             // Orange
  'Mechanical Permit': '#8B5CF6',      // Purple
  'Sprinkler Permit': '#EF4444',       // Red
  'Occupancy Permit': '#EC4899',       // Pink
  'Development Permit': '#14B8A6',     // Teal
  'Sign & Awning Permit': '#6366F1',   // Indigo
  'Tree Permit': '#84CC16',            // Lime
  'default': '#6B7280',                // Gray
};

const getMarkerIcon = (permitType) => {
  const color = permitTypeColors[permitType] || permitTypeColors.default;
  return createIcon(color);
};

/**
 * Map bounds adjuster component
 */
const MapBoundsAdjuster = ({ permits }) => {
  const map = useMap();

  useEffect(() => {
    if (permits && permits.length > 0) {
      const bounds = L.latLngBounds(
        permits.map(p => [p.lat, p.lng])
      );
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 });
    }
  }, [permits, map]);

  return null;
};

/**
 * PermitsPage - Map view of all permits
 */
const PermitsPage = () => {
  const [permits, setPermits] = useState([]);
  const [unmappedPermits, setUnmappedPermits] = useState([]);
  const [permitTypes, setPermitTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedType, setSelectedType] = useState('');
  const [selectedPermit, setSelectedPermit] = useState(null);
  const [stats, setStats] = useState(null);
  const mapRef = useRef(null);

  // Vancouver center (where permits are from)
  const defaultCenter = [49.2827, -123.1207];
  const defaultZoom = 12;

  useEffect(() => {
    fetchPermitTypes();
    fetchStats();
  }, []);

  useEffect(() => {
    fetchPermits();
  }, [selectedType]);

  const fetchPermitTypes = async () => {
    try {
      const response = await fetch(`${API_BASE}/permit-types`);
      const data = await response.json();
      setPermitTypes(data);
    } catch (err) {
      console.error('Error fetching permit types:', err);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/stats`);
      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  };

  const fetchPermits = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({ limit: 200 });
      if (selectedType) params.append('permit_type', selectedType);

      const response = await fetch(`${API_BASE}/permits/geocoded?${params}`);
      const data = await response.json();

      setPermits(data.permits || []);
      setUnmappedPermits(data.unmapped || []);
    } catch (err) {
      setError('Failed to load permits. Make sure the API server is running (py api.py)');
      console.error('Error fetching permits:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <div className="py-6 border-b border-border-color">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-text-primary">Permit Map</h1>
            <p className="text-text-secondary mt-1">
              {loading ? 'Loading...' : `${permits.length} permits with valid locations`}
            </p>
          </div>

          {/* Filter */}
          <div className="flex items-center gap-4">
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="px-4 py-2.5 bg-bg-card border border-border-color rounded-lg text-text-primary focus:outline-none focus:border-accent min-w-[200px]"
            >
              <option value="">All Permit Types</option>
              {permitTypes.map((pt) => (
                <option key={pt.type} value={pt.type}>
                  {pt.type} ({pt.count})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap gap-3 mt-4">
          {Object.entries(permitTypeColors)
            .filter(([key]) => key !== 'default')
            .slice(0, 8)
            .map(([type, color]) => (
              <div key={type} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: color }}
                />
                <span className="text-xs text-text-muted">
                  {type.replace(' Permit', '')}
                </span>
              </div>
            ))}
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="m-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Map Container */}
      <div className="flex-1 relative" style={{ minHeight: '600px' }}>
        {loading && (
          <div className="absolute inset-0 z-[1000] bg-bg-color/80 flex items-center justify-center">
            <div className="text-center">
              <div className="inline-block w-10 h-10 border-2 border-accent border-t-transparent rounded-full animate-spin" />
              <p className="mt-4 text-text-secondary">Geocoding permit addresses...</p>
              <p className="text-sm text-text-muted">This may take a moment</p>
            </div>
          </div>
        )}

        <MapContainer
          center={defaultCenter}
          zoom={defaultZoom}
          style={{ height: '100%', width: '100%', minHeight: '600px' }}
          ref={mapRef}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />

          {permits.map((permit) => (
            <Marker
              key={permit.id}
              position={[permit.lat, permit.lng]}
              icon={getMarkerIcon(permit.permit_type)}
              eventHandlers={{
                click: () => setSelectedPermit(permit),
              }}
            >
              <Popup className="permit-popup" maxWidth={350}>
                <div className="p-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: permitTypeColors[permit.permit_type] || permitTypeColors.default }}
                    />
                    <span className="text-xs font-medium text-gray-400">
                      {permit.permit_type}
                    </span>
                  </div>

                  <h3 className="font-bold text-white text-base mb-1">
                    {permit.permit_number}
                  </h3>

                  <p className="text-sm text-gray-300 mb-2">
                    {permit.primary_location}
                  </p>

                  <div className="flex gap-4 text-xs text-gray-400 mb-2">
                    <span>
                      <strong>Status:</strong> {permit.status}
                    </span>
                    <span>
                      <strong>Issued:</strong> {formatDate(permit.issue_date)}
                    </span>
                  </div>

                  {permit.work_description && (
                    <p className="text-xs text-gray-400 line-clamp-3 mb-2">
                      {permit.work_description.substring(0, 150)}...
                    </p>
                  )}

                  {permit.url && (
                    <a
                      href={permit.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-400 hover:underline"
                    >
                      View Original →
                    </a>
                  )}
                </div>
              </Popup>
            </Marker>
          ))}

          {permits.length > 0 && <MapBoundsAdjuster permits={permits} />}
        </MapContainer>
      </div>

      {/* Stats Bar */}
      {stats && (
        <div className="py-4 border-t border-border-color bg-bg-card">
          <div className="flex flex-wrap justify-center gap-8 text-sm">
            <div className="text-center">
              <span className="text-text-muted">Total in DB</span>
              <p className="text-xl font-bold text-text-primary">{stats.total_permits}</p>
            </div>
            <div className="text-center">
              <span className="text-text-muted">On Map</span>
              <p className="text-xl font-bold text-accent">{permits.length}</p>
            </div>
            <div className="text-center">
              <span className="text-text-muted">Unmapped</span>
              <p className="text-xl font-bold text-yellow-500">{unmappedPermits.length}</p>
            </div>
            <div className="text-center">
              <span className="text-text-muted">Latest Scrape</span>
              <p className="text-xl font-bold text-text-primary">
                {stats.recent_scrapes?.[0]?.[0] || '-'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Unmapped Permits Section */}
      {unmappedPermits.length > 0 && (
        <div className="py-6 border-t border-border-color">
          <h2 className="text-xl font-bold text-text-primary mb-4">
            Permits Unable to be Mapped ({unmappedPermits.length})
          </h2>
          <p className="text-text-muted text-sm mb-4">
            These permits could not be geocoded to a valid location in British Columbia.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-color">
                  <th className="text-left py-3 px-4 text-text-muted font-medium">Permit #</th>
                  <th className="text-left py-3 px-4 text-text-muted font-medium">Type</th>
                  <th className="text-left py-3 px-4 text-text-muted font-medium">Address</th>
                  <th className="text-left py-3 px-4 text-text-muted font-medium">Status</th>
                  <th className="text-left py-3 px-4 text-text-muted font-medium">Issue Date</th>
                  <th className="text-left py-3 px-4 text-text-muted font-medium">City</th>
                </tr>
              </thead>
              <tbody>
                {unmappedPermits.map((permit) => (
                  <tr key={permit.id} className="border-b border-border-color/50 hover:bg-bg-card/50">
                    <td className="py-3 px-4">
                      <span className="text-text-primary font-medium">{permit.permit_number}</span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <span
                          className="w-2 h-2 rounded-full"
                          style={{ backgroundColor: permitTypeColors[permit.permit_type] || permitTypeColors.default }}
                        />
                        <span className="text-text-secondary">{permit.permit_type}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-text-secondary">{permit.primary_location || '-'}</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 bg-bg-card rounded text-xs text-text-muted">
                        {permit.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-text-muted">{formatDate(permit.issue_date)}</td>
                    <td className="py-3 px-4 text-text-muted">{permit.source_city || 'Vancouver'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Custom Popup Styles */}
      <style>{`
        .permit-popup .leaflet-popup-content-wrapper {
          background: #1a1f2e;
          border: 1px solid #2d3748;
          border-radius: 8px;
        }
        .permit-popup .leaflet-popup-content {
          margin: 8px 12px;
          color: white;
        }
        .permit-popup .leaflet-popup-tip {
          background: #1a1f2e;
          border: 1px solid #2d3748;
        }
        .custom-marker {
          background: transparent !important;
          border: none !important;
        }
        .line-clamp-3 {
          display: -webkit-box;
          -webkit-line-clamp: 3;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
      `}</style>
    </div>
  );
};

export default PermitsPage;
