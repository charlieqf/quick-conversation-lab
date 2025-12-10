
import React, { useRef, useState } from 'react';
import { Calendar, Clock, FileBarChart, Trash2, CheckCircle2 } from 'lucide-react';
import { SessionReportData, Scenario, Role } from '../../../types';

interface HistoryItemProps {
  session: SessionReportData;
  scenario?: Scenario;
  role?: Role;
  isManageMode: boolean;
  isSelected: boolean;
  onToggleSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onViewReport: (data: SessionReportData) => void;
  onResume: (data: SessionReportData) => void;
}

export const HistoryItem: React.FC<HistoryItemProps> = ({ 
  session, 
  scenario, 
  role, 
  isManageMode,
  isSelected,
  onToggleSelect,
  onDelete,
  onViewReport,
  onResume
}) => {
  // Swipe Logic
  const touchStartX = useRef<number | null>(null);
  const [swipeOffset, setSwipeOffset] = useState(0);
  const DELETE_THRESHOLD = 80;

  const handleTouchStart = (e: React.TouchEvent) => {
    if (isManageMode) return;
    touchStartX.current = e.touches[0].clientX;
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (isManageMode || touchStartX.current === null) return;
    const diff = e.touches[0].clientX - touchStartX.current;
    
    // Only allow swiping left (negative diff)
    if (diff < 0) {
      // Limit swipe to reasonable amount
      setSwipeOffset(Math.max(diff, -120)); 
    }
  };

  const handleTouchEnd = () => {
    if (isManageMode) return;
    if (swipeOffset < -DELETE_THRESHOLD) {
      // Snap to open
      setSwipeOffset(-80);
    } else {
      // Snap back to close
      setSwipeOffset(0);
    }
    touchStartX.current = null;
  };

  const resetSwipe = () => {
    setSwipeOffset(0);
  };

  const formatTime = (iso: string) => {
    const d = new Date(iso);
    return `${d.getMonth() + 1}月${d.getDate()}日 ${d.getHours()}:${d.getMinutes().toString().padStart(2, '0')}`;
  };

  const durationStr = `${Math.floor(session.durationSeconds / 60)}分${session.durationSeconds % 60}秒`;
  
  // Grade Color
  const score = session.score;
  const gradeColor = score >= 90 ? 'text-yellow-500' : score >= 80 ? 'text-green-500' : score >= 60 ? 'text-blue-500' : 'text-orange-500';

  return (
    <div className="relative mb-3 overflow-hidden rounded-xl">
      
      {/* Background Delete Button (Revealed on Swipe) */}
      <div className="absolute inset-0 bg-red-500 flex items-center justify-end pr-5 rounded-xl">
        <button 
           onClick={() => onDelete(session.id)}
           className="flex flex-col items-center text-white"
        >
          <Trash2 className="w-5 h-5 mb-1" />
          <span className="text-[10px] font-bold">删除</span>
        </button>
      </div>

      {/* Main Content Card */}
      <div 
        className={`
          relative bg-white p-4 rounded-xl shadow-sm border border-slate-100 
          transition-transform duration-200 ease-out flex items-center
          ${isManageMode ? '' : 'active:bg-slate-50'}
        `}
        style={{ transform: `translateX(${swipeOffset}px)` }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        onClick={() => {
           if (swipeOffset < 0) resetSwipe();
           else if (isManageMode) onToggleSelect(session.id);
           // onResume(session); // Disabled
        }}
      >
        {/* Manage Mode Checkbox */}
        {isManageMode && (
          <div className="mr-3 flex-shrink-0 animate-in fade-in zoom-in duration-200">
             <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${isSelected ? 'bg-medical-500 border-medical-500' : 'border-slate-300'}`}>
                {isSelected && <CheckCircle2 className="w-3.5 h-3.5 text-white" />}
             </div>
          </div>
        )}

        <div className="flex-1 min-w-0">
           <div className="flex justify-between items-start mb-1">
              <h3 className="text-sm font-bold text-slate-800 truncate pr-2">
                 {scenario?.subtitle || '未知场景'}
              </h3>
              <div className={`text-sm font-black font-mono ${gradeColor}`}>
                 {score}
              </div>
           </div>
           
           <div className="flex items-center text-xs text-slate-500 mb-3">
              <span className="bg-slate-100 px-1.5 py-0.5 rounded text-[10px] mr-2 text-slate-600 font-medium">
                {role?.nameCN || 'Doctor'}
              </span>
              <span className="flex items-center mr-3">
                 <Calendar className="w-3 h-3 mr-1 opacity-70" /> {formatTime(session.startTime)}
              </span>
              <span className="flex items-center">
                 <Clock className="w-3 h-3 mr-1 opacity-70" /> {durationStr}
              </span>
           </div>

           {/* Action Buttons */}
           <div className="flex gap-2 relative z-10">
              <button 
                onClick={(e) => { e.stopPropagation(); onViewReport(session); }}
                className="flex items-center px-3 py-1.5 bg-slate-50 text-slate-600 text-[10px] font-medium rounded-lg border border-slate-200 hover:bg-slate-100 hover:text-medical-600 transition-colors w-full justify-center"
              >
                 <FileBarChart className="w-3 h-3 mr-1.5" />
                 查看报告
              </button>
           </div>
        </div>
      </div>
    </div>
  );
};
