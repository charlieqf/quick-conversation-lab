import React from 'react';
import { APIModel } from '../../../types';
import { Server, CheckCircle2, AlertCircle } from 'lucide-react';

interface ConnectionStatusProps {
  models: APIModel[];
  isLoading?: boolean;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ models, isLoading }) => {
  const backendConnected = models.length > 0;
  const activeModels = models.filter(m => m.isEnabled).length;

  return (
    <div className="mb-6 bg-white rounded-xl p-4 shadow-sm border border-slate-100">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
          <Server className="w-4 h-4 text-slate-500" />
          System Status
        </h3>
        <div className={`
          flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium
          ${backendConnected ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'}
        `}>
          <span className={`w-1.5 h-1.5 rounded-full ${backendConnected ? 'bg-emerald-500' : 'bg-rose-500'}`} />
          {backendConnected ? 'Backend Online' : 'Backend Offline'}
        </div>
      </div>

      <div className="space-y-3">
        {isLoading ? (
          <div className="text-xs text-slate-400 animate-pulse">Checking services...</div>
        ) : !backendConnected ? (
          <div className="text-xs text-rose-500 bg-rose-50 p-2 rounded">
            Cannot connect to Backend API. Is it running?
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2">
            {models.map(model => (
              <div key={model.id} className={`
                        flex items-center justify-between p-2 rounded border text-xs
                        ${model.isEnabled ? 'bg-slate-50 border-slate-100' : 'bg-slate-50 border-slate-100 opacity-60'}
                    `}>
                <div className="flex flex-col">
                  <span className="font-medium text-slate-700">{model.name}</span>
                  <span className="text-[10px] text-slate-400">{model.provider}</span>
                </div>

                {model.isEnabled ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                ) : (
                  <div className="group relative">
                    <AlertCircle className="w-4 h-4 text-amber-400 cursor-help" />
                    <div className="absolute bottom-full right-0 mb-2 w-max px-2 py-1 bg-slate-800 text-white text-[10px] rounded shadow opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                      Missing API Key
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {backendConnected && (
          <div className="mt-2 pt-2 border-t border-slate-50 flex justify-between items-center">
            <span className="text-[10px] text-slate-400">
              Active Adapters: {activeModels} / {models.length}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};