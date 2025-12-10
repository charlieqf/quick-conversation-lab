
import React, { useRef, useEffect, useState } from 'react';
import { LogEntry } from '../../../types';
import { Terminal, Trash2, ChevronUp, ChevronDown, CheckCircle2, AlertCircle, Radio } from 'lucide-react';

interface Props {
  logs: LogEntry[];
  onClear: () => void;
}

export const SessionDebugConsole: React.FC<Props> = ({ logs, onClear }) => {
  const [isExpanded, setIsExpanded] = useState(false); // Default collapsed
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current && isExpanded) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, isExpanded]);

  return (
    <div 
      className={`
        flex flex-col bg-white/95 border-t border-slate-200 text-xs font-mono 
        transition-all duration-300 ease-in-out backdrop-blur-md shadow-[0_-4px_15px_-3px_rgba(0,0,0,0.05)]
        ${isExpanded ? 'h-72' : 'h-9'}
      `}
    >
      {/* Header - Click to toggle */}
      <div 
        className="flex items-center justify-between px-3 py-2 bg-slate-50/80 border-b border-slate-200 cursor-pointer select-none hover:bg-slate-100 transition-colors h-9"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center text-slate-500 gap-2">
          {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
          <div className="flex items-center">
            <Terminal className="w-3.5 h-3.5 mr-2 text-medical-600" />
            <span className="font-bold text-slate-700">Realtime Logs</span>
            
            {/* Last Log Preview when collapsed */}
            {!isExpanded && logs.length > 0 && (
               <div className="ml-3 flex items-center text-[10px] bg-white px-2 py-0.5 rounded-full border border-slate-200 shadow-sm max-w-[200px]">
                 <div className={`w-1.5 h-1.5 rounded-full mr-1.5 flex-shrink-0 ${
                    logs[logs.length-1].type === 'error' ? 'bg-red-500' : 'bg-green-500'
                 }`}></div>
                 <span className="truncate text-slate-600 font-sans">
                   {logs[logs.length-1].message}
                 </span>
               </div>
            )}
          </div>
        </div>
        
        <div className="flex items-center gap-3">
            <span className="text-[10px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">{logs.length} events</span>
            <button 
                onClick={(e) => { e.stopPropagation(); onClear(); }} 
                className="text-slate-400 hover:text-red-500 hover:bg-red-50 p-1 rounded transition-all"
                title="Clear Logs"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1.5 scroll-smooth bg-white" ref={scrollRef}>
        {logs.map((log, i) => (
          <div key={i} className="flex items-start space-x-2 border-b border-slate-50 pb-1.5 last:border-0 group">
             <span className="text-[10px] text-slate-400 shrink-0 font-sans mt-0.5">{log.timestamp.split(' ')[1]}</span>
             
             {/* Icon based on type */}
             <div className="mt-0.5 flex-shrink-0">
               {log.type === 'error' ? <AlertCircle className="w-3 h-3 text-red-500" /> :
                log.type === 'success' ? <CheckCircle2 className="w-3 h-3 text-green-500" /> :
                log.type === 'stream' ? <Radio className="w-3 h-3 text-blue-400" /> :
                <div className="w-1 h-1 rounded-full bg-slate-300 m-1" />}
             </div>

             <span className={`break-all leading-tight ${
               log.type === 'error' ? 'text-red-600 bg-red-50 px-1 rounded' : 
               log.type === 'success' ? 'text-green-700' : 
               log.type === 'stream' ? 'text-blue-600' : 'text-slate-600'
             }`}>
               {log.message}
             </span>
          </div>
        ))}
        {logs.length === 0 && isExpanded && (
            <div className="flex flex-col items-center justify-center h-full text-slate-400 opacity-60">
              <Terminal className="w-8 h-8 mb-2 stroke-1" />
              <div className="text-xs italic">等待连接...</div>
            </div>
        )}
      </div>
    </div>
  );
};
