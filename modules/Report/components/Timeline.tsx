
import React from 'react';
import { ChatMessage } from '../../../types';
import { ThumbsUp, ThumbsDown, Minus, MessageSquare } from 'lucide-react';
import { Button } from '../../../components/ui/Button';

interface TimelineProps {
  messages: ChatMessage[];
  onViewTranscript: () => void;
}

export const Timeline: React.FC<TimelineProps> = ({ messages, onViewTranscript }) => {
  // Filter for feedback items, and find the preceding user message for context
  const feedbackItems = messages.map((msg, index) => {
    if (msg.type !== 'feedback') return null;
    
    // Find context: Look backwards for the last user message
    let contextMsg = '';
    for (let i = index - 1; i >= 0; i--) {
      if (messages[i].role === 'user') {
        contextMsg = messages[i].content;
        break;
      }
    }

    return {
      ...msg,
      context: contextMsg
    };
  }).filter(item => item !== null) as (ChatMessage & { context: string })[];

  if (feedbackItems.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 bg-slate-50 rounded-lg border border-slate-100 border-dashed">
        <p className="text-slate-400 text-xs italic mb-3">本次演练未触发任何关键评分点。</p>
        <Button 
          variant="secondary" 
          onClick={onViewTranscript} 
          className="text-xs h-9 bg-white shadow-sm hover:text-medical-600 hover:border-medical-200"
          icon={<MessageSquare className="w-3.5 h-3.5"/>}
        >
           查看完整对话记录
        </Button>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Header Action for non-empty state */}
      <div className="absolute -top-10 right-0">
          <button 
             onClick={onViewTranscript}
             className="flex items-center text-[10px] font-medium text-slate-400 hover:text-medical-600 bg-slate-50 px-2 py-1 rounded-md transition-colors"
          >
             <MessageSquare className="w-3 h-3 mr-1.5" />
             完整对话
          </button>
      </div>

      <div className="relative pl-4 space-y-6 before:absolute before:left-1.5 before:top-2 before:bottom-0 before:w-px before:bg-slate-200">
        {feedbackItems.map((item) => {
          const isPositive = (item.scoreDelta || 0) > 0;
          const isNegative = (item.scoreDelta || 0) < 0;
          
          return (
            <div key={item.id} className="relative animate-in slide-in-from-bottom-2 duration-500">
               {/* Dot on Timeline */}
               <div className={`
                 absolute -left-4 top-1 w-3 h-3 rounded-full border-2 border-white shadow-sm z-10
                 ${isPositive ? 'bg-green-500' : isNegative ? 'bg-red-500' : 'bg-slate-400'}
               `}></div>

               <div className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                  {/* Header: Score & Reason */}
                  <div className="flex justify-between items-start mb-2">
                     <div className="flex items-center space-x-2">
                        {isPositive ? <ThumbsUp className="w-3.5 h-3.5 text-green-600" /> : isNegative ? <ThumbsDown className="w-3.5 h-3.5 text-red-600" /> : <Minus className="w-3.5 h-3.5 text-slate-400"/>}
                        <span className={`text-xs font-bold ${isPositive ? 'text-green-700' : isNegative ? 'text-red-700' : 'text-slate-600'}`}>
                           {isPositive ? '加分项' : isNegative ? '减分项' : '反馈'}
                        </span>
                     </div>
                     <span className={`text-xs font-mono font-bold ${isPositive ? 'text-green-600' : isNegative ? 'text-red-600' : 'text-slate-500'}`}>
                        {item.scoreDelta && item.scoreDelta > 0 ? '+' : ''}{item.scoreDelta}
                     </span>
                  </div>

                  <p className="text-sm text-slate-800 font-medium mb-2 leading-snug">
                     {item.reason}
                  </p>

                  {/* Context Quote */}
                  {item.context && (
                     <div className="bg-white p-2 rounded border border-slate-200 text-xs text-slate-500 italic relative">
                        <span className="absolute top-1 left-1 text-slate-300 text-xl leading-none">“</span>
                        <span className="pl-3 block line-clamp-2">{item.context}</span>
                     </div>
                  )}
               </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
