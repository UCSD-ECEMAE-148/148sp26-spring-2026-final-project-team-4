import React, { useEffect, useState } from 'react'

export default function ImageGallery({ missionId }) {
  const [images, setImages] = useState([])
  const [annotations, setAnnotations] = useState([])

  useEffect(() => {
    fetch(`/api/missions/${missionId}`).then(r => r.json()).then(d => {
      setImages(d.images || [])
      setAnnotations(d.annotations || [])
    })
  }, [missionId])

  const annByFile = {}
  (annotations || []).forEach(a => {
    const f = a.get ? a.get('filename') : a.filename
    annByFile[f] = a
  })

  return (
    <div>
      <h4>Images</h4>
      <div className="grid">
        {images.map(fn => (
          <div className="card" key={fn}>
            <img src={`/api/missions/${missionId}/images/${fn}`} alt={fn} />
            <div className="meta">
              <strong>{fn}</strong>
              <div>{annByFile[fn] ? annByFile[fn].description || '' : ''}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
