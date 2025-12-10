
import React from 'react';
import { Trophy, Clock, Calendar } from 'lucide-react';

interface ScoreHeaderProps {
  score: number;
  startTime: string;
  duration: number;
}

export const ScoreHeader: React.FC<ScoreHeaderProps> = ({ score, startTime, duration }) => {
  // Calculate Grade
  let grade = 'C';
  let gradeColor = 'text-slate-500';
  let bgGradient = 'from-slate-700 to-slate-900';
  let advice = '仍有很大提升空间';

  if (score >= 90) {
    grade = 'S';
    gradeColor = 'text-yellow-400';
    bgGradient = 'from-medical-600 to-medical-800';
    advice = '完美表现，令人印象深刻！';
  } else if (score >= 80) {
    grade = 'A';
    gradeColor = 'text-green-400';
    bgGradient = 'from-emerald-600 to-emerald-800';
    advice = '表现优秀，继续保持。';
  } else if (score >= 60) {
    grade = 'B';
    gradeColor = 'text-blue-400';
    bgGradient = 'from-blue-600 to-blue-800';
    advice = '合格，但细节需注意。';
  } else {
    bgGradient = 'from-orange-600 to-red-800';
    gradeColor = 'text-white';
    advice = '建议重新复习关键知识点。';
  }

  const formatDuration = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}分${s}秒`;
  };

  const formatDate = (iso: string) => {
    return new Date(iso).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className={`relative pt-8 pb-12 px-6 overflow-hidden bg-gradient-to-br ${bgGradient} text-white`}>
      {/* Background Decor */}
      <div className="absolute top-0 right-0 p-4 opacity-10">
        <Trophy className="w-32 h-32" />
      </div>

      <div className="relative z-10">
        <div className="flex justify-between items-start mb-6">
          <div>
             <h1 className="text-lg font-bold opacity-90">评估报告</h1>
             <div className="flex items-center text-xs opacity-60 mt-1 space-x-3">
               <span className="flex items-center"><Calendar className="w-3 h-3 mr-1" /> {formatDate(startTime)}</span>
               <span className="flex items-center"><Clock className="w-3 h-3 mr-1" /> {formatDuration(duration)}</span>
             </div>
          </div>
          <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-lg px-3 py-1 text-center">
             <div className={`text-2xl font-black ${gradeColor} font-serif leading-none`}>{grade}</div>
             <div className="text-[10px] opacity-70 uppercase tracking-widest">Level</div>
          </div>
        </div>

        <div className="flex items-baseline">
           <span className="text-5xl font-bold tracking-tight">{score}</span>
           <span className="text-lg opacity-60 ml-1">/100</span>
        </div>
        <p className="text-sm mt-2 opacity-80 font-medium">
           {advice}
        </p>
      </div>
    </div>
  );
};
