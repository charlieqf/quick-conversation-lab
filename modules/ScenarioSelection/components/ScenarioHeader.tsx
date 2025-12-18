
import React, { useState, useEffect } from 'react';
import { Plus } from 'lucide-react';
import { Button } from '../../../components/ui/Button';
import { UserProfile } from '../../../types';

interface ScenarioHeaderProps {
  userProfile: UserProfile;
  onNewScenario: () => void;
  isReadOnly?: boolean;
}

export const ScenarioHeader: React.FC<ScenarioHeaderProps> = ({ userProfile, onNewScenario, isReadOnly = false }) => {
  const [greeting, setGreeting] = useState('');
  const [dateString, setDateString] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const hour = now.getHours();

      if (hour < 6) setGreeting('夜深了');
      else if (hour < 11) setGreeting('早上好');
      else if (hour < 13) setGreeting('中午好');
      else if (hour < 18) setGreeting('下午好');
      else setGreeting('晚上好');

      const dateOptions: Intl.DateTimeFormatOptions = {
        month: 'long',
        day: 'numeric',
        weekday: 'long'
      };
      // Force Chinese locale
      setDateString(new Intl.DateTimeFormat('zh-CN', dateOptions).format(now));
    };

    updateTime();
  }, []);

  return (
    <div className="bg-white px-5 py-6 border-b border-slate-100 shadow-sm sticky top-0 z-10">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight flex items-center">
            {greeting}，{userProfile.name}
          </h1>
          <p className="text-xs font-medium text-medical-600 uppercase tracking-wider mt-1">
            {dateString}
          </p>
        </div>
        {!isReadOnly && (
          <div className="flex-shrink-0">
            <button
              onClick={onNewScenario}
              className="w-10 h-10 bg-medical-50 text-medical-600 rounded-full flex items-center justify-center border border-medical-100 shadow-sm active:scale-95 transition-all"
              aria-label="新建场景"
            >
              <Plus className="w-6 h-6" />
            </button>
          </div>
        )}
      </div>
      <p className="text-slate-500 text-sm">
        选择一个临床场景开始您的模拟训练或评估。
      </p>
    </div>
  );
};