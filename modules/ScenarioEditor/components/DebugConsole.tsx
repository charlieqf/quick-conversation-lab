
import React, { useState, useRef, useEffect } from 'react';
import { Terminal, ChevronDown, ChevronUp, Trash2, Eye, EyeOff, AlertCircle, CheckCircle2 } from 'lucide-react';
import { LogEntry } from '../../../types';

interface DebugConsoleProps {
  logs: LogEntry[];
  onClear: () => void;
}

const LogItem: React.FC<{ log: LogEntry }> = ({ log }) => {
  const [showDetail, setShowDetail] = useState(false);

  return (
    <div className="animate-in fade-in duration-300 border-b border-slate-800/50 pb-1 mb-1 last:border-0">
      <div className="flex items-start space-x-2">
        <span className="text-slate-500 flex-shrink-0 font-mono text-[10px] mt-0.5">[{log.timestamp}]</span>
        <div className="flex-1 min-w-0">
          <div className={`break-words text-[11px] ${
            log.type === 'error' ? 'text-red-400' :
            log.type === 'success' ? 'text-green-400' :
            log.type === 'stream' ? 'text-cyan-200' :
            'text-slate-300'
          }`}>
            {log.type === 'stream' && <span className="mr-1 opacity-50">&gt;</span>}
            {log.message}
          </div>
          
          {log.detail && (
            <button 
              onClick={() => setShowDetail(!showDetail)}
              className="mt-1 flex items-center text-[10px] text-slate-500 hover:text-slate-300 transition-colors focus:outline-none"
            >
              {showDetail ? <EyeOff className="w-3 h-3 mr-1" /> : <Eye className="w-3 h-3 mr-1" />}
              {showDetail ? '收起详情' : '查看详情'}
            </button>
          )}
          
          {showDetail && log.detail && (
            <pre className="mt-2 p-2 bg-slate-950 rounded text-[10px] font-mono text-slate-400 overflow-x-auto whitespace-pre-wrap border border-slate-800">
              {log.detail}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
};

export const DebugConsole: React.FC<DebugConsoleProps> = ({ logs, onClear }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, isExpanded]);

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden bg-slate-900 text-slate-300 shadow-sm mt-4 flex flex-col transition-all duration-300">
      {/* Header */}
      <div 
        className="flex items-center justify-between px-3 py-2 bg-slate-800 cursor-pointer select-none border-b border-slate-700"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-medical-400" />
          <span className="text-xs font-bold text-slate-100">Debug Console</span>
          <div className={`flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium ${logs.some(l => l.type === 'error') ? 'bg-red-900/50 text-red-200' : 'bg-slate-700 text-slate-300'}`}>
            {logs.some(l => l.type === 'error') && <AlertCircle className="w-3 h-3 mr-1" />}
            {logs.length} Logs
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <button 
            onClick={(e) => { e.stopPropagation(); onClear(); }}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded transition-colors"
            title="Clear Console"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
          <div className="text-slate-500">
            {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
          </div>
        </div>
      </div>

      {/* Content */}
      {isExpanded && (
        <div 
          ref={scrollRef}
          className="h-64 overflow-y-auto p-3 space-y-2 scroll-smooth bg-slate-900"
        >
          {logs.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-600 space-y-2 opacity-60">
              <Terminal className="w-8 h-8" />
              <p className="text-xs italic">等待任务开始...</p>
            </div>
          ) : (
            logs.map((log, index) => (
              <LogItem key={index} log={log} />
            ))
          )}
        </div>
      )}
    </div>
  );
};
