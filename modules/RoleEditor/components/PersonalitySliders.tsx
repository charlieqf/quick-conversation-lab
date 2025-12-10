
import React from 'react';

interface SliderProps {
  label: string;
  leftLabel: string;
  rightLabel: string;
  value: number;
  onChange: (val: number) => void;
  colorClass: string;
}

const Slider: React.FC<SliderProps> = ({ label, leftLabel, rightLabel, value, onChange, colorClass }) => (
  <div className="mb-6">
    <div className="flex justify-between items-center mb-2">
      <label className="text-xs font-bold text-slate-700">{label}</label>
      <span className={`text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-100 ${colorClass}`}>
        {value}%
      </span>
    </div>
    <input
      type="range"
      min="0"
      max="100"
      value={value}
      onChange={(e) => onChange(Number(e.target.value))}
      className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-slate-600 hover:accent-medical-600 transition-all"
    />
    <div className="flex justify-between text-[10px] text-slate-400 mt-1 font-medium">
      <span>{leftLabel}</span>
      <span>{rightLabel}</span>
    </div>
  </div>
);

interface PersonalitySlidersProps {
  hostility: number;
  verbosity: number;
  skepticism: number;
  onChange: (key: 'hostility' | 'verbosity' | 'skepticism', val: number) => void;
}

export const PersonalitySliders: React.FC<PersonalitySlidersProps> = ({
  hostility, verbosity, skepticism, onChange
}) => {
  return (
    <div className="bg-white p-5 rounded-xl border border-slate-100 shadow-sm">
      <h3 className="text-sm font-bold text-slate-800 mb-4 flex items-center">
        <span className="w-1 h-4 bg-medical-500 rounded mr-2"></span>
        性格参数调优 (Personality Tuner)
      </h3>
      
      <Slider 
        label="配合度 (Agreeableness)" 
        leftLabel="敌对/Hostile" 
        rightLabel="友好/Friendly" 
        value={hostility} 
        onChange={(v) => onChange('hostility', v)} 
        colorClass={hostility < 30 ? 'text-red-600' : 'text-green-600'}
      />

      <Slider 
        label="健谈程度 (Verbosity)" 
        leftLabel="简短/Brief" 
        rightLabel="话痨/Verbose" 
        value={verbosity} 
        onChange={(v) => onChange('verbosity', v)} 
        colorClass="text-blue-600"
      />

      <Slider 
        label="怀疑程度 (Skepticism)" 
        leftLabel="轻信/Gullible" 
        rightLabel="刁钻/Skeptic" 
        value={skepticism} 
        onChange={(v) => onChange('skepticism', v)} 
        colorClass={skepticism > 70 ? 'text-orange-600' : 'text-slate-600'}
      />
    </div>
  );
};
