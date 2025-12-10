import React from 'react';
import { ChatMessage, ScoringDimension } from '../../../types';

interface RadarChartProps {
  messages: ChatMessage[];
  scoringCriteria?: string;
  scoringDimensions?: ScoringDimension[];
  // Optional: Directly provided scores (e.g. from AI Re-evaluation)
  customEvaluation?: { label: string; score: number; comment: string }[];
}

export const RadarChart: React.FC<RadarChartProps> = ({ messages, scoringCriteria, scoringDimensions, customEvaluation }) => {
  
  // Internal Type
  interface ChartItem {
    id: string;
    label: string;
    score: number;
    analysis: string;
  }

  let scores: ChartItem[] = [];

  // BRANCH A: Use Custom Evaluation (AI Re-eval)
  if (customEvaluation && customEvaluation.length > 0) {
    scores = customEvaluation.map(item => ({
      id: item.label,
      label: item.label,
      score: item.score,
      analysis: item.comment || '暂无详细评语'
    }));
  } 
  // BRANCH B: Calculate from Messages (Real-time logs)
  else {
    // 1. Determine Labels (Dimensions)
    let labels: string[] = [];

    // Priority A: Use configured dimensions
    if (scoringDimensions && scoringDimensions.length > 0) {
      labels = scoringDimensions.map(d => d.label);
    } else if (scoringCriteria) {
      // Priority B: Fallback regex extraction
      // Regex 1: Bold headers (e.g. **Clinical Judgment**:)
      const boldRegex = /\*\*([^*]+)\*\*[:：]/g;
      let match;
      while ((match = boldRegex.exec(scoringCriteria)) !== null) {
        if (match[1].length < 30) labels.push(match[1].trim());
      }

      // Regex 2: Markdown Headers (e.g. ### Communication)
      if (labels.length === 0) {
        const headerRegex = /#{1,4}\s+([^:\n]+)/g;
        while ((match = headerRegex.exec(scoringCriteria)) !== null) {
            const candidate = match[1].trim();
            if (!candidate.includes('评分') && !candidate.includes('Scoring') && candidate.length < 30) {
              labels.push(candidate);
            }
        }
      }
    }

    // Fallback defaults if parsing fails or text is empty
    if (labels.length < 3) {
      labels = ['Communication', 'Clinical Reasoning', 'Professionalism', 'Empathy', 'Efficiency'];
    }
    
    // Deduplicate
    labels = [...new Set(labels)];

    // 2. Map Dimensions to Objects and Aggregate Feedback
    scores = labels.map(label => {
      // Start with a baseline.
      let rawScore = 60; 
      const feedbackReasons: string[] = [];
      
      messages.filter(m => m.type === 'feedback').forEach(m => {
        // Check if this message belongs to this dimension
        let isMatch = false;
        
        // Prioritize explicit dimension tag from tool call
        if (m.dimension && m.dimension === label) {
          isMatch = true;
        } 
        // Fallback to keyword matching if legacy message or matching fail
        else if (!m.dimension && m.reason) {
          if (m.reason.toLowerCase().includes(label.toLowerCase())) {
              isMatch = true;
          }
        }

        if (isMatch) {
          rawScore += (m.scoreDelta || 0);
          if (m.reason) feedbackReasons.push(m.reason);
        }
      });

      return { 
        id: label,
        label: label,
        score: Math.min(100, Math.max(20, rawScore)),
        analysis: feedbackReasons.length > 0 ? feedbackReasons.join('; ') : '暂无特定评语'
      };
    });
  }

  // 4. SVG Generation Helpers
  const size = 200;
  const center = size / 2;
  const radius = 70;
  // Handle empty case
  const dimCount = scores.length > 0 ? scores.length : 5; 
  const angleSlice = (Math.PI * 2) / dimCount;

  const getPoint = (score: number, index: number) => {
    const value = score / 100; // Normalize 0-1
    const angle = index * angleSlice - Math.PI / 2; // Start from top
    const r = radius * value;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle)
    };
  };

  const pointsString = scores.map((s, i) => {
    const p = getPoint(s.score, i);
    return `${p.x},${p.y}`;
  }).join(' ');

  return (
    <div className="flex flex-col items-center justify-center">
      {/* Chart Visual */}
      <div className="relative w-full max-w-[240px] aspect-square mb-6">
        <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-full">
          {/* Background Webs (20%, 40%, 60%, 80%, 100%) */}
          {[0.2, 0.4, 0.6, 0.8, 1].map((scale, idx) => (
             <polygon
               key={idx}
               points={scores.map((_, i) => {
                 const angle = i * angleSlice - Math.PI / 2;
                 const r = radius * scale;
                 return `${center + r * Math.cos(angle)},${center + r * Math.sin(angle)}`;
               }).join(' ')}
               fill="none"
               stroke="#e2e8f0"
               strokeWidth="1"
             />
          ))}

          {/* Axes */}
          {scores.map((_, i) => {
             const p = getPoint(100, i);
             return (
               <line 
                 key={i} 
                 x1={center} y1={center} 
                 x2={p.x} y2={p.y} 
                 stroke="#e2e8f0" 
                 strokeWidth="1" 
               />
             );
          })}

          {/* Data Polygon */}
          {scores.length > 0 && (
            <polygon
              points={pointsString}
              fill="rgba(13, 148, 136, 0.2)" // Medical-600 with opacity
              stroke="#0d9488"
              strokeWidth="2"
            />
          )}

          {/* Data Points */}
          {scores.map((s, i) => {
            const p = getPoint(s.score, i);
            return (
              <circle 
                key={i} 
                cx={p.x} cy={p.y} r="3" 
                fill="#0d9488" 
                stroke="white" 
                strokeWidth="1"
              />
            );
          })}

          {/* Labels on Chart */}
          {scores.map((s, i) => {
             // Push labels out a bit further than radius
             const labelRadius = radius + 20; 
             const angle = i * angleSlice - Math.PI / 2;
             const x = center + labelRadius * Math.cos(angle);
             const y = center + labelRadius * Math.sin(angle);
             
             // Anchor adjustment based on position
             const anchor = x < center - 10 ? 'end' : x > center + 10 ? 'start' : 'middle';
             
             return (
               <text
                 key={i}
                 x={x} y={y}
                 textAnchor={anchor}
                 dominantBaseline="middle"
                 className="text-[8px] fill-slate-500 font-medium"
                 style={{ fontSize: '9px' }}
               >
                 {s.label.length > 15 ? s.label.substring(0, 12) + '...' : s.label}
               </text>
             );
          })}
        </svg>
      </div>

      {/* Detailed Analysis Table (Subject | Score | Analysis) */}
      <div className="w-full border-t border-slate-100">
         <table className="w-full text-left text-xs">
            <thead>
               <tr className="border-b border-slate-100">
                  <th className="py-2 pl-2 font-bold text-slate-600 w-1/4">科目</th>
                  <th className="py-2 font-bold text-slate-600 w-1/6 text-center">得分</th>
                  <th className="py-2 pr-2 font-bold text-slate-600">解析</th>
               </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
               {scores.map((s, index) => (
                  <tr key={index}>
                     <td className="py-2 pl-2 align-top text-slate-800 font-medium pr-2">
                        {s.label}
                     </td>
                     <td className="py-2 align-top text-center">
                        <span className={`font-bold ${s.score >= 80 ? 'text-green-600' : s.score >= 60 ? 'text-blue-600' : 'text-orange-600'}`}>
                           {s.score}
                        </span>
                     </td>
                     <td className="py-2 pr-2 align-top text-slate-500 leading-relaxed">
                        {s.analysis}
                     </td>
                  </tr>
               ))}
            </tbody>
         </table>
      </div>
    </div>
  );
};