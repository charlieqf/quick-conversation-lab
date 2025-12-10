import React from 'react';
import { Zap, CheckCircle2, AlertCircle, ExternalLink } from 'lucide-react';
import { Button } from '../../../components/ui/Button';

interface ConnectionStatusProps {
  isConnected: boolean;
  onConnect: () => void;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ isConnected, onConnect }) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm mb-6">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className={`p-1.5 rounded-full ${isConnected ? 'bg-green-100' : 'bg-slate-100'}`}>
            <Zap className={`w-4 h-4 ${isConnected ? 'text-green-600 fill-current' : 'text-slate-400'}`} />
          </div>
          <h3 className="font-bold text-slate-800 text-sm">连接状态</h3>
        </div>
        <div className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${isConnected ? 'bg-green-50 text-green-700' : 'bg-slate-100 text-slate-500'}`}>
          {isConnected ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>已连接</span>
            </>
          ) : (
            <>
              <AlertCircle className="w-3.5 h-3.5" />
              <span>未配置</span>
            </>
          )}
        </div>
      </div>

      <p className="text-xs text-slate-500 mb-4 leading-relaxed">
        本应用使用 Wanyi API 进行驱动。
        {isConnected 
          ? ' API Key 已就绪，您可以正常使用所有 AI 功能。' 
          : ' 请连接您的 Google Cloud Project 以启用 AI 场景生成与对话功能。'}
      </p>

      {!isConnected && (
        <Button 
          variant="primary" 
          onClick={onConnect} 
          className="w-full justify-center bg-medical-600 hover:bg-medical-700"
          icon={<ExternalLink className="w-4 h-4" />}
        >
          连接 Google AI Studio
        </Button>
      )}
      
      {isConnected && (
        <div className="bg-slate-50 rounded px-3 py-2 text-xs font-mono text-slate-500 border border-slate-100 flex justify-between items-center">
          <span>API Key Configured</span>
          <span className="text-green-600 text-[10px] flex items-center">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500 mr-1.5"></span>
            Active
          </span>
        </div>
      )}
    </div>
  );
};