
import React, { useState } from 'react';
import { ArrowLeft, Mic, Power, Activity, Settings } from 'lucide-react';
import { SessionReportData } from '../../types';
import { useSessionConnection } from './hooks/useSessionConnection';
import { ConfigPanel } from './components/ConfigPanel';
import { WaveformCanvas } from './components/WaveformCanvas';
import { SessionDebugConsole } from './components/SessionDebugConsole';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';

interface ActiveSessionModuleProps {
  scenarioId: string;
  roleId: string;
  onExit: () => void;
  onComplete: (data: SessionReportData) => void;
}

export const ActiveSessionModule: React.FC<ActiveSessionModuleProps> = ({ 
  scenarioId, 
  roleId, 
  onExit,
  onComplete 
}) => {
  const { 
    status, 
    connect, 
    disconnect, 
    endSessionAndGetReport,
    config, 
    setConfig, 
    logs, 
    clearLogs, 
    volume 
  } = useSessionConnection(scenarioId, roleId);

  const [isConfigOpen, setIsConfigOpen] = useState(false);

  const isConnected = status === 'connected';

  const handleFinish = () => {
    const report = endSessionAndGetReport();
    onComplete(report);
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 text-slate-900 relative">
      {/* Header - Light Theme */}
      <div className="bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between shadow-sm sticky top-0 z-20">
        <button onClick={() => { disconnect(); onExit(); }} className="text-slate-500 hover:text-slate-800 transition-colors p-1.5 hover:bg-slate-100 rounded-full">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex flex-col items-center">
          <div className="flex items-center space-x-2 text-sm font-bold text-slate-800">
            <Activity className={`w-4 h-4 ${isConnected ? 'text-medical-600' : 'text-slate-400'}`} />
            <span>Smart Coach (Live)</span>
          </div>
          <div className={`text-[10px] font-mono font-medium ${isConnected ? 'text-medical-600' : 'text-slate-400'}`}>
            {status.toUpperCase()}
          </div>
        </div>
        <button 
          onClick={() => setIsConfigOpen(true)}
          className="text-slate-400 hover:text-medical-600 transition-colors p-1.5 rounded-full hover:bg-slate-100"
        >
          <Settings className="w-5 h-5" />
        </button>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col relative overflow-hidden">
        
        {/* Center Area: Just Clean or Start Button */}
        <div className="flex-1 flex items-center justify-center relative bg-slate-50 overflow-hidden">
          
          {!isConnected && (
            <div className="absolute inset-0 flex items-center justify-center bg-white/40 backdrop-blur-[2px] z-10">
              <div className="flex flex-col items-center animate-in fade-in zoom-in duration-300">
                <Button 
                  onClick={connect} 
                  className="bg-medical-600 hover:bg-medical-700 shadow-xl shadow-medical-600/30 px-10 py-5 rounded-full text-lg border-4 border-white"
                  isLoading={status === 'connecting'}
                  icon={<Mic className="w-6 h-6" />}
                >
                  {status === 'connecting' ? '连接中...' : '开始会话'}
                </Button>
              </div>
            </div>
          )}
          
          {isConnected && (
             <div className="flex flex-col items-center justify-center text-slate-300 animate-pulse">
                <Mic className="w-16 h-16 mb-4 opacity-20" />
                <p className="text-sm font-medium">Listening...</p>
             </div>
          )}
        </div>

        {/* Debug Console - Bottom Overlay */}
        <div className="absolute bottom-0 left-0 right-0 z-30">
          <SessionDebugConsole logs={logs} onClear={clearLogs} />
        </div>
      </div>

      {/* Footer Controls - Floating above console */}
      {isConnected && (
        <div className="absolute bottom-12 left-0 right-0 flex flex-col items-center justify-end pb-safe z-40 pointer-events-none">
           
           {/* Waveform Visualization - Now above the button */}
           <div className="mb-4 pointer-events-auto">
             <WaveformCanvas 
                volume={volume} 
                active={isConnected} 
                color="#0d9488" 
             />
           </div>

           <button 
             onClick={handleFinish}
             className="w-16 h-16 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center shadow-lg shadow-red-500/40 active:scale-95 transition-all pointer-events-auto border-4 border-white ring-1 ring-slate-100"
           >
             <Power className="w-8 h-8" />
           </button>
        </div>
      )}

      {/* Config Modal */}
      <Modal
        isOpen={isConfigOpen}
        onClose={() => setIsConfigOpen(false)}
        title="会话参数配置"
        footer={
          <Button variant="primary" onClick={() => setIsConfigOpen(false)}>
            完成
          </Button>
        }
      >
        <ConfigPanel config={config} onChange={setConfig} />
      </Modal>
    </div>
  );
};
