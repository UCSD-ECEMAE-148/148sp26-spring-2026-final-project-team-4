import React, { useEffect, useState } from 'react'
import MissionMap from './components/MissionMap'
import ImageGallery from './components/ImageGallery'
import MissionReport from './components/MissionReport'

export default function App() {
  const [missions, setMissions] = useState([])
  const [selected, setSelected] = useState(null)
  const [tab, setTab] = useState('map')

  useEffect(() => {
    fetch('/api/missions').then(r => r.json()).then(d => setMissions(d.missions || []))
  }, [])

  useEffect(() => {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${proto}//${location.host}/ws/status`)
    ws.onmessage = (e) => {
      console.log('status', e.data)
    }
    return () => ws.close()
  }, [])

  return (
    <div className="app">
      <div className="sidebar">
        <h3>Missions</h3>
        <ul>
          {missions.map(m => (
            <li key={m} onClick={() => setSelected(m)} className={selected===m? 'active':''}>{m}</li>
          ))}
        </ul>
      </div>
      <div className="content">
        {!selected && <div className="placeholder">Select a mission</div>}
        {selected && (
          <div>
            <div className="tabs">
              <button onClick={() => setTab('map')} className={tab==='map'?'on':''}>Map</button>
              <button onClick={() => setTab('images')} className={tab==='images'?'on':''}>Images</button>
              <button onClick={() => setTab('report')} className={tab==='report'?'on':''}>Report</button>
            </div>
            <div className="panel">
              {tab === 'map' && <MissionMap missionId={selected} />}
              {tab === 'images' && <ImageGallery missionId={selected} />}
              {tab === 'report' && <MissionReport missionId={selected} />}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
