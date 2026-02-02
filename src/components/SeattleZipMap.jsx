import React, { useMemo, useEffect, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, GeoJSON, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import seattleZipData from '../data/seattle-zip-codes.json';

/**
 * Component to handle map zoom changes
 */
const MapZoomHandler = ({ selectedZips, layersRef, defaultCenter, defaultZoom }) => {
  const map = useMap();

  useEffect(() => {
    if (selectedZips && selectedZips.length > 0) {
      // Combine bounds of all selected zips
      let combinedBounds = null;
      selectedZips.forEach(zip => {
        if (layersRef.current[zip]) {
          const layer = layersRef.current[zip];
          const bounds = layer.getBounds();
          if (combinedBounds) {
            combinedBounds.extend(bounds);
          } else {
            combinedBounds = bounds;
          }
        }
      });
      if (combinedBounds) {
        map.fitBounds(combinedBounds, { padding: [50, 50], maxZoom: 13 });
      }
    } else {
      // Reset to default view
      map.setView(defaultCenter, defaultZoom);
    }
  }, [selectedZips, map, layersRef, defaultCenter, defaultZoom]);

  return null;
};

/**
 * Tier color configuration for map polygons
 * Premium = purple, High = yellow, Low = red, Bonus = grey
 */
const tierColors = {
  'Premium': {
    fillColor: '#A855F7',
    color: '#A855F7',
    fillOpacity: 0.3,
  },
  'High': {
    fillColor: '#EAB308',
    color: '#EAB308',
    fillOpacity: 0.3,
  },
  'Low': {
    fillColor: '#EF4444',
    color: '#EF4444',
    fillOpacity: 0.3,
  },
  'Bonus (low activity)': {
    fillColor: '#6B7280',
    color: '#6B7280',
    fillOpacity: 0.3,
  },
};

const tierLabels = {
  'Premium': 'Premium',
  'High': 'High',
  'Low': 'Low',
  'Bonus (low activity)': 'Bonus',
};

/**
 * SeattleZipMap component - Static map showing zip code coverage
 * Uses Leaflet with OpenStreetMap tiles and embedded GeoJSON boundaries
 * Supports linked hover states and click-to-zoom with external components
 */
const SeattleZipMap = ({ zipCodes, hoveredZips = [], selectedZips = [], onHover, onSelect }) => {
  const layersRef = useRef({});

  // Create a lookup map for zip code tiers
  const zipTierMap = useMemo(() => {
    const map = {};
    zipCodes.forEach((zip) => {
      map[zip.code] = zip.tier;
    });
    return map;
  }, [zipCodes]);

  // Filter GeoJSON to only include zip codes we serve
  const filteredGeoData = useMemo(() => {
    const filteredFeatures = seattleZipData.features.filter((feature) => {
      const zipCode = feature.properties.ZCTA5CE10 || feature.properties.GEOID10;
      return zipTierMap[zipCode];
    });

    return {
      type: 'FeatureCollection',
      features: filteredFeatures,
    };
  }, [zipTierMap]);

  // Seattle center coordinates
  // Latitude (first value): increase to shift view north, decrease to shift south
  const seattleCenter = [47.62, -122.3321];
  const defaultZoom = 11;

  // Get base style for a zip code based on its tier
  const getBaseStyle = useCallback((zipCode) => {
    const tier = zipTierMap[zipCode];
    const style = tierColors[tier] || tierColors['High'];

    return {
      fillColor: style.fillColor,
      weight: 2,
      opacity: 1,
      color: style.color,
      fillOpacity: style.fillOpacity,
    };
  }, [zipTierMap]);

  // Style function for GeoJSON features based on tier, hover, and selection state
  const getStyle = useCallback((feature) => {
    const zipCode = feature.properties.ZCTA5CE10 || feature.properties.GEOID10;
    const baseStyle = getBaseStyle(zipCode);
    const isHovered = hoveredZips.includes(zipCode);
    const isSelected = selectedZips.includes(zipCode);
    const isHighlighted = isHovered || isSelected;
    const hasFocus = hoveredZips.length > 0 || selectedZips.length > 0;

    if (hasFocus) {
      if (isHighlighted) {
        return {
          ...baseStyle,
          weight: 3,
          fillOpacity: 0.5,
        };
      } else {
        return {
          ...baseStyle,
          opacity: 0.3,
          fillOpacity: 0.1,
        };
      }
    }

    return baseStyle;
  }, [getBaseStyle, hoveredZips, selectedZips]);

  // Update all layer styles when hoveredZips or selectedZips changes
  useEffect(() => {
    const hasFocus = hoveredZips.length > 0 || selectedZips.length > 0;

    Object.entries(layersRef.current).forEach(([zipCode, layer]) => {
      const isHovered = hoveredZips.includes(zipCode);
      const isSelected = selectedZips.includes(zipCode);
      const isHighlighted = isHovered || isSelected;

      if (hasFocus) {
        if (isHighlighted) {
          layer.setStyle({
            ...getBaseStyle(zipCode),
            weight: 3,
            fillOpacity: 0.5,
          });
        } else {
          layer.setStyle({
            ...getBaseStyle(zipCode),
            opacity: 0.3,
            fillOpacity: 0.1,
          });
        }
      } else {
        layer.setStyle(getBaseStyle(zipCode));
      }
    });
  }, [hoveredZips, selectedZips, getBaseStyle]);

  // Hover and click effects for each feature
  const onEachFeature = useCallback((feature, layer) => {
    const zipCode = feature.properties.ZCTA5CE10 || feature.properties.GEOID10;
    const tier = zipTierMap[zipCode];

    // Store layer reference
    layersRef.current[zipCode] = layer;

    const tierLabel = tierLabels[tier] || 'N/A';

    layer.bindTooltip(
      `<div class="font-bold">${zipCode}</div><div>${tierLabel}</div>`,
      { sticky: true, className: 'zip-tooltip' }
    );

    layer.on({
      mouseover: () => {
        if (onHover) {
          onHover(zipCode);
        }
      },
      mouseout: () => {
        if (onHover) {
          onHover(null);
        }
      },
      click: () => {
        if (onSelect) {
          onSelect(zipCode);
        }
      },
    });
  }, [zipTierMap, onHover, onSelect]);

  return (
    <div className="w-full h-full rounded-xl overflow-hidden border border-border-color relative">
      {/* Zoom Out Button - appears when zoomed in */}
      {selectedZips.length > 0 && (
        <button
          onClick={() => onSelect(null)}
          className="absolute top-3 left-3 z-[1000] bg-bg-card hover:bg-bg-card-hover border border-border-color rounded-lg p-2 transition-all duration-200 hover:scale-105 shadow-lg"
          title="Zoom out"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-text-primary"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
            <line x1="8" y1="11" x2="14" y2="11" />
          </svg>
        </button>
      )}
      <MapContainer
        center={seattleCenter}
        zoom={defaultZoom}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={false}
        zoomControl={false}
        dragging={false}
        touchZoom={false}
        doubleClickZoom={false}
        boxZoom={false}
        keyboard={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        {filteredGeoData.features.length > 0 && (
          <GeoJSON
            data={filteredGeoData}
            style={getStyle}
            onEachFeature={onEachFeature}
            key={JSON.stringify(zipTierMap)}
          />
        )}
        <MapZoomHandler
          selectedZips={selectedZips}
          layersRef={layersRef}
          defaultCenter={seattleCenter}
          defaultZoom={defaultZoom}
        />
      </MapContainer>
    </div>
  );
};

export default SeattleZipMap;
