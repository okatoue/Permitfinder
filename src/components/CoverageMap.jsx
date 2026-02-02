import React, { useState, useMemo } from 'react';
import SeattleZipMap from './SeattleZipMap';
import pricebookData from '../data/pricebook_merged.json';

/**
 * Module selector button component
 */
const ModuleButton = ({ module, label, isActive, onClick }) => {
  return (
    <button
      onClick={() => onClick(module)}
      className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all duration-200
        ${isActive
          ? 'bg-accent text-accent-text'
          : 'bg-bg-card border border-border-color text-text-secondary hover:text-text-primary hover:border-text-muted'
        }`}
    >
      {label}
    </button>
  );
};

/**
 * Tier configuration for colors
 * Premium = purple, High = yellow, Low = red, Bonus = grey
 */
const tierConfig = {
  'Premium': {
    borderClass: 'border-[#A855F7]',
    textClass: 'text-[#A855F7]',
    label: 'Premium',
    ringClass: 'ring-[#A855F7]',
    color: '#A855F7',
  },
  'High': {
    borderClass: 'border-[#EAB308]',
    textClass: 'text-[#EAB308]',
    label: 'High',
    ringClass: 'ring-[#EAB308]',
    color: '#EAB308',
  },
  'Low': {
    borderClass: 'border-[#EF4444]',
    textClass: 'text-[#EF4444]',
    label: 'Low',
    ringClass: 'ring-[#EF4444]',
    color: '#EF4444',
  },
  'Bonus (low activity)': {
    borderClass: 'border-[#6B7280]',
    textClass: 'text-[#6B7280]',
    label: 'Bonus',
    ringClass: 'ring-[#6B7280]',
    color: '#6B7280',
  },
  'null': {
    borderClass: 'border-[#333] opacity-50',
    textClass: 'text-text-muted',
    label: 'N/A',
    ringClass: 'ring-[#333]',
    color: '#333333',
  },
};

/**
 * ZipGroupCard component for coverage grid - displays a group of zip codes
 */
const ZipGroupCard = ({ group, isHovered, isFaded, isSelected, onMouseEnter, onMouseLeave, onClick }) => {
  const config = tierConfig[group.tier] || tierConfig['null'];

  return (
    <div
      className="-m-1.5 p-1.5 cursor-pointer"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      onClick={onClick}
    >
      <div
        className={`bg-[#0F131A] border rounded-md p-3 text-center transition-all duration-200
          ${config.borderClass}
          ${isHovered || isSelected ? 'scale-105 shadow-lg' : ''}
          ${isSelected ? `ring-2 ${config.ringClass} ring-offset-1 ring-offset-bg-color` : ''}
          ${isFaded && !isSelected ? 'opacity-30 scale-[0.97]' : 'opacity-100'}
        `}
      >
        <span className="block font-bold text-text-primary mb-1 text-sm leading-tight">
          {group.zips.join(', ')}
        </span>
        <span className={`text-[0.7rem] uppercase font-bold tracking-wide ${config.textClass}`}>
          {config.label}
        </span>
        {group.price > 0 && (
          <span className="block text-[0.65rem] text-text-muted mt-1">
            ${group.price}/mo
          </span>
        )}
      </div>
    </div>
  );
};

/**
 * Legend component for tier colors
 */
const TierLegend = () => {
  const tiers = [
    { key: 'Premium', color: '#A855F7', label: 'Premium' },
    { key: 'High', color: '#EAB308', label: 'High' },
    { key: 'Low', color: '#EF4444', label: 'Low' },
    { key: 'Bonus (low activity)', color: '#6B7280', label: 'Bonus' },
  ];

  return (
    <div className="flex flex-wrap gap-4 justify-center mt-4">
      {tiers.map((tier) => (
        <div key={tier.key} className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded-sm"
            style={{ backgroundColor: tier.color }}
          />
          <span className="text-xs text-text-muted">{tier.label}</span>
        </div>
      ))}
    </div>
  );
};

/**
 * CoverageMap component - Displays zip code groups and interactive map side by side
 * Hover states and click-to-zoom are linked between the zip code boxes and map polygons
 */
const CoverageMap = () => {
  const [hoveredGroupId, setHoveredGroupId] = useState(null);
  const [selectedGroupId, setSelectedGroupId] = useState(null);
  const [selectedModule, setSelectedModule] = useState('weeds');

  // Get zip code groups for the selected module, sorted by tier priority
  const { zipGroups, zipToGroupMap } = useMemo(() => {
    const tierOrder = { 'Premium': 0, 'High': 1, 'Low': 2, 'Bonus (low activity)': 3 };

    // Filter by module and valid tier
    const moduleEntries = pricebookData
      .filter(entry => entry.module === selectedModule && entry.tier && entry.tier !== '')
      .sort((a, b) => {
        const orderA = tierOrder[a.tier] ?? 5;
        const orderB = tierOrder[b.tier] ?? 5;
        if (orderA !== orderB) return orderA - orderB;
        return b.annual_unique_total_2025 - a.annual_unique_total_2025; // Higher leads first within tier
      });

    // Create groups with unique IDs
    const groups = moduleEntries.map((entry, index) => {
      const zips = entry.ZIP.split(',').map(z => z.trim());
      return {
        id: `group-${index}`,
        zips,
        tier: entry.tier,
        price: entry.monthly_price_usd,
        leadsPerMonth: entry.expected_leads_per_month,
      };
    });

    // Create a map from individual zip to its group
    const zipMap = {};
    groups.forEach(group => {
      group.zips.forEach(zip => {
        zipMap[zip] = group;
      });
    });

    return { zipGroups: groups, zipToGroupMap: zipMap };
  }, [selectedModule]);

  // Get all individual zips with their tier info for the map
  const zipCodesForMap = useMemo(() => {
    return Object.entries(zipToGroupMap).map(([zip, group]) => ({
      code: zip,
      tier: group.tier,
      groupId: group.id,
    }));
  }, [zipToGroupMap]);

  // Get the currently hovered/selected zips for the map
  const hoveredZips = useMemo(() => {
    if (!hoveredGroupId) return [];
    const group = zipGroups.find(g => g.id === hoveredGroupId);
    return group ? group.zips : [];
  }, [hoveredGroupId, zipGroups]);

  const selectedZips = useMemo(() => {
    if (!selectedGroupId) return [];
    const group = zipGroups.find(g => g.id === selectedGroupId);
    return group ? group.zips : [];
  }, [selectedGroupId, zipGroups]);

  const handleSelect = (groupId) => {
    setSelectedGroupId(selectedGroupId === groupId ? null : groupId);
  };

  // Handle hover from map (individual zip)
  const handleMapHover = (zipCode) => {
    if (zipCode && zipToGroupMap[zipCode]) {
      setHoveredGroupId(zipToGroupMap[zipCode].id);
    } else {
      setHoveredGroupId(null);
    }
  };

  // Handle selection from map (individual zip)
  const handleMapSelect = (zipCode) => {
    if (zipCode && zipToGroupMap[zipCode]) {
      const groupId = zipToGroupMap[zipCode].id;
      setSelectedGroupId(selectedGroupId === groupId ? null : groupId);
    } else {
      setSelectedGroupId(null);
    }
  };

  const modules = [
    { key: 'weeds', label: 'Weeds' },
    { key: 'dumping', label: 'Dumping' },
    { key: 'vacant', label: 'Vacant' },
  ];

  return (
    <div>
      {/* Module Selector */}
      <div className="flex justify-center gap-3 mb-6">
        {modules.map((module) => (
          <ModuleButton
            key={module.key}
            module={module.key}
            label={module.label}
            isActive={selectedModule === module.key}
            onClick={setSelectedModule}
          />
        ))}
      </div>

      {/* Tier Legend */}
      <TierLegend />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-6">
        {/* ZIP Grid - Left */}
        <div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {zipGroups.map((group) => (
              <ZipGroupCard
                key={group.id}
                group={group}
                isHovered={hoveredGroupId === group.id}
                isFaded={(hoveredGroupId !== null && hoveredGroupId !== group.id) || (selectedGroupId !== null && hoveredGroupId === null && selectedGroupId !== group.id)}
                isSelected={selectedGroupId === group.id}
                onMouseEnter={() => setHoveredGroupId(group.id)}
                onMouseLeave={() => setHoveredGroupId(null)}
                onClick={() => handleSelect(group.id)}
              />
            ))}
          </div>
        </div>

        {/* Map - Right */}
        <div className="h-[40vh] lg:h-auto">
          <SeattleZipMap
            zipCodes={zipCodesForMap}
            hoveredZips={hoveredZips}
            selectedZips={selectedZips}
            onHover={handleMapHover}
            onSelect={handleMapSelect}
          />
        </div>
      </div>
    </div>
  );
};

export default CoverageMap;
