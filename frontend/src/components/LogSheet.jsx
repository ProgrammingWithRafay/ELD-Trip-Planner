import React from 'react';

// Duty statuses mapping to Y-axis coordinates on the grid
const STATUS_ROWS = {
  off_duty: 0,
  sleeper_berth: 1,
  driving: 2,
  on_duty_not_driving: 3
};

const ROW_LABELS = [
  "Off Duty",
  "Sleeper Berth",
  "Driving",
  "On Duty"
];

export default function LogSheet({ log, index }) {
  // SVG drawing dimensions
  const width = 800;
  const height = 160;
  const xOffset = 120; // Space for left labels
  const yOffset = 40;  // Space for top header (hours)
  const chartWidth = width - xOffset - 20; // 20px right margin
  const chartHeight = height - yOffset - 20; // 20px bottom margin
  const rowHeight = chartHeight / 4;
  
  const getX = (hr) => xOffset + (hr / 24) * chartWidth;
  const getY = (status) => yOffset + (STATUS_ROWS[status] * rowHeight) + (rowHeight / 2);

  // Generate the path for the line graph
  let pathD = "";
  if (log.segments && log.segments.length > 0) {
    const firstSeg = log.segments[0];
    pathD += `M ${getX(firstSeg.start_hr)} ${getY(firstSeg.status)}`;
    
    for (let i = 0; i < log.segments.length; i++) {
      const seg = log.segments[i];
      // Draw horizontal line for this segment
      pathD += ` L ${getX(seg.end_hr)} ${getY(seg.status)}`;
      
      // If there's a next segment, draw vertical connector
      if (i < log.segments.length - 1) {
        const nextSeg = log.segments[i + 1];
        pathD += ` L ${getX(seg.end_hr)} ${getY(nextSeg.status)}`;
      }
    }
  }

  // Hours for the X-axis
  const hours = [];
  for (let i = 0; i <= 24; i++) {
    hours.push(i);
  }

  // Find transitions for remarks
  const remarks = [];
  if (log.segments) {
    for (let i = 0; i < log.segments.length; i++) {
      const seg = log.segments[i];
      if (seg.label && seg.label !== "Driving" && seg.label !== "Rest") {
        remarks.push({ hr: seg.start_hr, label: seg.label });
      }
    }
  }

  return (
    <div className="card" style={{ marginBottom: '2rem' }}>
      <div className="flex justify-between items-center mb-4" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '1.25rem', color: 'var(--primary)' }}>Day {log.day}</h3>
          <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
            <strong>Carrier:</strong> Sample Carrier LLC &nbsp;|&nbsp; <strong>Truck:</strong> Unit 001
          </div>
        </div>
        <div className="flex gap-4" style={{ fontSize: '0.875rem', fontFamily: 'var(--font-mono)' }}>
          <div className="flex flex-col items-center">
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>OFF</span>
            <span style={{ fontWeight: 600 }}>{log.total_off_duty_hr.toFixed(1)}h</span>
          </div>
          <div className="flex flex-col items-center">
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>SB</span>
            <span style={{ fontWeight: 600 }}>{log.total_sleeper_hr.toFixed(1)}h</span>
          </div>
          <div className="flex flex-col items-center">
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>DRV</span>
            <span style={{ fontWeight: 600 }}>{log.total_driving_hr.toFixed(1)}h</span>
          </div>
          <div className="flex flex-col items-center">
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>ON</span>
            <span style={{ fontWeight: 600 }}>{log.total_on_duty_hr.toFixed(1)}h</span>
          </div>
        </div>
      </div>
      
      <div style={{ overflowX: 'auto', paddingBottom: '2rem' }}>
        <svg 
          viewBox={`0 0 ${width} ${height + 100}`} 
          style={{ minWidth: '800px', width: '100%', display: 'block', backgroundColor: 'var(--surface-color)' }}
        >
          {/* Grid lines and row labels */}
          {ROW_LABELS.map((label, i) => (
            <g key={`row-${i}`}>
              <text 
                x={xOffset - 10} 
                y={yOffset + (i * rowHeight) + (rowHeight / 2) + 4} 
                textAnchor="end"
                style={{ fontSize: '12px', fill: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}
              >
                {label}
              </text>
              {/* Horizontal grid line */}
              <line 
                x1={xOffset} y1={yOffset + i * rowHeight} 
                x2={width - 20} y2={yOffset + i * rowHeight} 
                stroke="var(--border-color)" strokeWidth="1" 
              />
            </g>
          ))}
          {/* Bottom horizontal line */}
          <line 
            x1={xOffset} y1={yOffset + 4 * rowHeight} 
            x2={width - 20} y2={yOffset + 4 * rowHeight} 
            stroke="var(--border-color)" strokeWidth="1" 
          />

          {/* Hour columns */}
          {hours.map(hr => (
            <g key={`col-${hr}`}>
              {/* Vertical line */}
              <line 
                x1={getX(hr)} y1={yOffset} 
                x2={getX(hr)} y2={yOffset + chartHeight} 
                stroke={hr % 12 === 0 ? "var(--text-secondary)" : "var(--border-color)"} 
                strokeWidth={hr % 12 === 0 ? "2" : "1"} 
              />
              {/* Top hour label */}
              <text 
                x={getX(hr)} y={yOffset - 10} 
                textAnchor="middle"
                style={{ fontSize: '11px', fill: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}
              >
                {hr === 0 ? 'M' : hr === 12 ? 'N' : hr === 24 ? 'M' : hr > 12 ? hr - 12 : hr}
              </text>
            </g>
          ))}

          {/* Draw the log path */}
          {pathD && (
            <path 
              d={pathD} 
              fill="none" 
              stroke="var(--primary)" 
              strokeWidth="4" 
              strokeLinejoin="round"
            />
          )}

          {/* Remarks */}
          <g transform={`translate(0, ${height})`}>
            {remarks.map((remark, i) => (
              <g key={`remark-${i}`} transform={`translate(${getX(remark.hr)}, 10)`}>
                <line x1="0" y1="-10" x2="0" y2="5" stroke="var(--primary)" strokeWidth="1" />
                <text 
                  x="5" y="15" 
                  transform="rotate(45)"
                  style={{ fontSize: '11px', fill: 'var(--text-primary)', fontFamily: 'var(--font-body)' }}
                >
                  {remark.label}
                </text>
              </g>
            ))}
          </g>
        </svg>
      </div>
    </div>
  );
}
