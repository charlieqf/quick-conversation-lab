
import React from 'react';
import { SessionConfig } from '../types';
import { Settings2 } from 'lucide-react';

interface Props {
  config: SessionConfig;
  onChange: (cfg: SessionConfig) => void;
}

export const ConfigPanel: React.FC<Props> = ({ config, onChange }) => {
  return (
    <div className="text-slate-700">
      <div className="flex items-center text-xs font-bold mb-4 text-slate-500 bg-slate-50 p-2 rounded">
        <Settings2 className="w-3.5 h-3.5 mr-2" />
        <span>Stream Configuration (Native)</span>
      </div>

      <div className="space-y-5 px-1">
        <div>
          <label className="text-xs font-bold text-slate-700 block mb-1">采样率 (Sample Rate)</label>
          <p className="text-[10px] text-slate-400 mb-2">Gemini Live 原生支持 24kHz。</p>
          <select
            value={config.sampleRate}
            onChange={(e) => onChange({ ...config, sampleRate: Number(e.target.value) as any })}
            className="w-full bg-white border border-slate-200 text-sm rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-medical-500"
          >
            <option value={16000}>16000 Hz (Standard)</option>
            <option value={16000}>16000 Hz (Standard)</option>
          </select>
        </div>

        <div>
          <div className="flex justify-between items-center mb-1">
            <label className="text-xs font-bold text-slate-700 block">缓冲区大小 (Buffer Size)</label>
            <span className="text-[10px] font-mono text-medical-600 font-bold">{config.bufferThreshold * 40}ms</span>
          </div>
          <p className="text-[10px] text-slate-400 mb-2">增加缓冲可提高稳定性，减少缓冲可降低延迟。</p>

          <input
            type="range" min="1" max="10" step="1"
            value={config.bufferThreshold}
            onChange={(e) => onChange({ ...config, bufferThreshold: Number(e.target.value) })}
            className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-medical-600"
          />
          <div className="flex justify-between text-[10px] text-slate-400 mt-1">
            <span>Low Latency</span>
            <span>High Stability</span>
          </div>
        </div>
      </div>
    </div>
  );
};
