import React from 'react'

export default function MissionMap({ missionId }) {
  const src = `/api/missions/${missionId}/map.png`
  return (
    <div>
      <h4>Map</h4>
      <img src={src} alt="map" style={{ maxWidth: '100%', height: 'auto', border: '1px solid #ccc' }} />
    </div>
  )
}
