import React, { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'

export default function MissionReport({ missionId }) {
  const [report, setReport] = useState('')

  useEffect(() => {
    fetch(`/api/missions/${missionId}`).then(r => r.json()).then(d => setReport(d.report || ''))
  }, [missionId])

  return (
    <div>
      <h4>Report</h4>
      <div className="report"><ReactMarkdown>{report}</ReactMarkdown></div>
    </div>
  )
}
