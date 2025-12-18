
import React, { useEffect, useState } from 'react';
import { List, Sparkles, Save, X } from 'lucide-react';
import { SessionReportData, Scenario, Role, LogEntry, AiEvaluationResult } from '../../types';
import { ScoreHeader } from './components/ScoreHeader';
import { RadarChart } from './components/RadarChart';
import { Timeline } from './components/Timeline';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { DebugConsole } from '../ScenarioEditor/components/DebugConsole';
import { useAuth } from '../../contexts/AuthContext';

interface ReportModuleProps {
   data: SessionReportData;
   onExit: () => void;
   onRetry: () => void;
}

const DEFAULT_EVAL_PROMPT = `Role: Senior Medical Examiner.
Task: Re-evaluate the trainee (Doctor) in the following medical simulation.

[SCENARIO CONTEXT]
{{SCENARIO_INFO}}

[SCORING CRITERIA]
{{SCORING_CRITERIA}}

[TARGET DIMENSIONS]
{{DIMENSIONS_LIST}}

[TRANSCRIPT]
{{TRANSCRIPT}}

INSTRUCTIONS:
1. Review the transcript against the criteria.
2. Score the trainee (0-100) for EACH target dimension provided above.
3. Provide a brief specific comment (MUST BE IN CHINESE) for each dimension justifying the score.
4. Provide an overall summary (MUST BE IN CHINESE).
5. Calculate an overall weighted total score.
6. Output STRICTLY valid JSON.

JSON Format:
{
  "totalScore": number,
  "summary": "Overall analysis in Chinese",
  "dimensions": [
    { "label": "Exact Label from Target List", "score": number, "comment": "Analysis comment in Chinese" }
  ]
}`;

export const ReportModule: React.FC<ReportModuleProps> = ({ data, onExit, onRetry }) => {
   const { token } = useAuth();
   const [scenario, setScenario] = useState<Scenario | null>(null);
   const [role, setRole] = useState<Role | null>(null);

   // Re-evaluation State
   // Initialize from persisted analysis if available
   const [aiEvaluation, setAiEvaluation] = useState<AiEvaluationResult | null>(data.aiAnalysis || null);
   const [displayScore, setDisplayScore] = useState(data.aiAnalysis ? data.aiAnalysis.totalScore : data.score);

   // Track if we have a new, unsaved evaluation
   const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

   const [isEvalModalOpen, setIsEvalModalOpen] = useState(false);
   const [isTranscriptOpen, setIsTranscriptOpen] = useState(false);

   // Load saved prompt or default
   const [evalPromptTemplate, setEvalPromptTemplate] = useState(DEFAULT_EVAL_PROMPT);

   // Load Prompt from API
   useEffect(() => {
      const loadSettings = async () => {
         if (!token) return;
         try {
            const res = await fetch('/api/users/profile', {
               headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
               const profile = await res.json();
               if (profile.settings && profile.settings.evalPrompt) {
                  setEvalPromptTemplate(profile.settings.evalPrompt);
               }
            }
         } catch (e) {
            console.error("Failed to load evaluation prompt", e);
         }
      };
      loadSettings();
   }, [token]);

   const [isEvaluating, setIsEvaluating] = useState(false);
   const [logs, setLogs] = useState<LogEntry[]>([]);

   useEffect(() => {
      const loadContext = async () => {
         if (!token) return;
         try {
            // Fetch from API
            const [resScen, resRole] = await Promise.all([
               fetch(`/api/data/scenarios/${data.scenarioId}`, { headers: { 'Authorization': `Bearer ${token}` } }),
               fetch(`/api/data/roles/${data.roleId}`, { headers: { 'Authorization': `Bearer ${token}` } })
            ]);

            if (resScen.ok) {
               const s = await resScen.json();
               setScenario(s);
            }
            if (resRole.ok) {
               const r = await resRole.json();
               setRole(r);
            }
         } catch (e) {
            console.error("Failed to load context for report", e);
         }
      };

      if (data.scenarioId && data.roleId) {
         loadContext();
      }
   }, [data, token]);

   const addLog = (message: string, type: LogEntry['type'] = 'info', detail?: string) => {
      const timestamp = new Date().toLocaleTimeString('zh-CN', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
      setLogs(prev => [...prev, { timestamp, message, type, detail }]);
   };

   const getDimensionLabels = (scen: Scenario): string[] => {
      if (scen.scoringDimensions && scen.scoringDimensions.length > 0) {
         return scen.scoringDimensions.map(d => d.label);
      }

      const criteria = scen.scoringCriteria || '';
      const labels: string[] = [];
      const boldRegex = /\*\*([^*]+)\*\*[:：]/g;
      let match;
      while ((match = boldRegex.exec(criteria)) !== null) {
         if (match[1].length < 30) labels.push(match[1].trim());
      }

      if (labels.length === 0) {
         const headerRegex = /#{1,4}\s+([^:\n]+)/g;
         while ((match = headerRegex.exec(criteria)) !== null) {
            const candidate = match[1].trim();
            if (!candidate.includes('评分') && !candidate.includes('Scoring') && candidate.length < 30) {
               labels.push(candidate);
            }
         }
      }

      if (labels.length < 3) return ['Communication', 'Clinical Reasoning', 'Professionalism', 'Empathy'];
      return [...new Set(labels)];
   };

   const handleReEvaluate = async () => {
      if (!scenario || !token) return;

      setLogs([]); // Clear previous logs
      setIsEvaluating(true);
      addLog('初始化评估任务...', 'info');

      try {
         let selectedModel = 'gemini-2.5-flash';
         let currentSettings: any = {};

         const resProfile = await fetch('/api/users/profile', {
            headers: { 'Authorization': `Bearer ${token}` }
         });
         if (resProfile.ok) {
            const profile = await resProfile.json();
            currentSettings = profile.settings || {};
            if (currentSettings.selectedScenarioModel) {
               selectedModel = currentSettings.selectedScenarioModel;
            }
         }

         const modelDisplayName = selectedModel.includes('pro') ? 'Wanyi Pro' : 'Wanyi Flash';
         addLog(`使用 AI 模型: ${modelDisplayName}`, 'info');

         // Save Prompt to API (Async, don't block)
         if (evalPromptTemplate !== currentSettings.evalPrompt) {
            fetch('/api/users/profile', {
               method: 'PUT',
               headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${token}`
               },
               body: JSON.stringify({
                  settings: {
                     ...currentSettings,
                     evalPrompt: evalPromptTemplate
                  }
               })
            }).catch(console.error);
         }

         addLog('准备上下文数据 (Transcript & Criteria)...', 'info');
         const transcript = data.messages
            .filter(m => m.type === 'text')
            .map(m => `${m.role === 'user' ? 'Doctor' : role?.name || 'Patient'}: ${m.content}`)
            .join('\n');

         const scenarioInfo = `Title: ${scenario.title}\nDescription: ${scenario.description}`;
         const dimensionList = getDimensionLabels(scenario).join(', ');

         const prompt = evalPromptTemplate
            .replace('{{SCENARIO_INFO}}', scenarioInfo)
            .replace('{{SCORING_CRITERIA}}', scenario.scoringCriteria || 'General Medical Standard')
            .replace('{{DIMENSIONS_LIST}}', dimensionList)
            .replace('{{TRANSCRIPT}}', transcript);

         addLog('构建 Prompt 完成，发送请求至 Backend API...', 'info');

         // Call Backend API
         const res = await fetch('/api/models/tools/scenario-generate', {
            method: 'POST',
            headers: {
               'Content-Type': 'application/json',
               'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
               model: selectedModel,
               contents: [{ parts: [{ text: prompt }] }],
               generation_config: { response_mime_type: 'application/json' }
            })
         });

         if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || `Server Error: ${res.status}`);
         }

         const responseData = await res.json();
         const fullText = responseData.text;

         addLog('接收到响应数据', 'info', fullText);

         let result: AiEvaluationResult;
         try {
            result = JSON.parse(fullText);
         } catch (e) {
            addLog('JSON解析失败，尝试修复...', 'info');
            // Simple cleanup for common markdown block issues
            const jsonMatch = fullText.match(/```json\n([\s\S]*?)\n```/) || fullText.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
               result = JSON.parse(jsonMatch[1] || jsonMatch[0]);
            } else {
               throw new Error("Could not parse JSON from response");
            }
         }

         if (typeof result.totalScore !== 'number' || !Array.isArray(result.dimensions)) {
            throw new Error("Invalid JSON structure: Missing totalScore or dimensions array.");
         }

         const newScore = Number(result.totalScore);
         const summary = result.summary || "未提供详细分析";

         addLog('评估完成 (Evaluation Success)', 'success', `【最终得分】: ${newScore}\n【分析结果】: ${summary}`);

         setDisplayScore(newScore);
         setAiEvaluation(result);
         setHasUnsavedChanges(true);

      } catch (e: any) {
         console.error("Evaluation failed", e);
         addLog(`评估过程发生错误: ${e.message}`, 'error', e.stack);
         alert("评估失败，请查看 Debug 窗口日志。");
      } finally {
         setIsEvaluating(false);
      }
   };

   const handleSaveResult = async () => {
      if (!aiEvaluation || !token) return;

      try {
         const res = await fetch(`/api/history/${data.id}`, {
            method: 'PUT',
            headers: {
               'Content-Type': 'application/json',
               'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
               score: aiEvaluation.totalScore,
               aiAnalysis: aiEvaluation
            })
         });

         if (res.ok) {
            addLog('评估结果已成功保存到后端！', 'success');
            setHasUnsavedChanges(false);
            setTimeout(() => {
               setIsEvalModalOpen(false);
            }, 800);
         } else {
            addLog(`保存失败: ${res.statusText}`, 'error');
         }
      } catch (e: any) {
         addLog(`保存失败: ${e.message}`, 'error');
      }
   };

   return (
      <div className="min-h-full bg-slate-50 flex flex-col relative pb-24">

         {/* 1. Header & Score */}
         <ScoreHeader score={displayScore} startTime={data.startTime} duration={data.durationSeconds} />

         <div className="px-4 -mt-6 z-10 space-y-6">

            {/* 2. Context Info Card */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-4">
               {/* Header Row with Action */}
               <div className="flex justify-between items-center mb-2">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">演练场景</h3>
                  <button
                     onClick={() => setIsEvalModalOpen(true)}
                     className="flex items-center text-[10px] font-bold text-medical-600 bg-medical-50 hover:bg-medical-100 px-3 py-1.5 rounded-full transition-colors border border-medical-200 active:scale-95 shadow-sm"
                     title="使用 AI 重新评估本次会话"
                  >
                     <Sparkles className="w-3.5 h-3.5 mr-1.5" />
                     AI 评估
                  </button>
               </div>

               <div className="flex items-start justify-between">
                  <div>
                     <p className="text-base font-bold text-slate-800">{scenario?.subtitle || '未知场景'}</p>
                     <p className="text-xs text-slate-500 mt-0.5">{scenario?.title}</p>
                  </div>
                  <div className="text-right">
                     <p className="text-sm font-bold text-medical-600">{role?.nameCN || 'Doctor'}</p>
                     <p className="text-[10px] text-slate-400">{role?.title}</p>
                  </div>
               </div>
            </div>

            {/* 3. Radar Chart (Dimensions) */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-4 overflow-hidden">
               <h3 className="text-sm font-bold text-slate-800 mb-4 flex items-center">
                  <span className="w-1 h-4 bg-purple-500 rounded mr-2"></span>
                  能力维度分析 (Capability Radar)
               </h3>
               <RadarChart
                  messages={data.messages}
                  scoringCriteria={scenario?.scoringCriteria}
                  scoringDimensions={scenario?.scoringDimensions}
                  customEvaluation={aiEvaluation ? aiEvaluation.dimensions : undefined} // Pass the structured AI result
               />
               {aiEvaluation && (
                  <p className="text-[10px] text-medical-600 mt-2 text-center bg-medical-50 py-1 rounded">
                     *数据来源: AI 智能重评
                  </p>
               )}
               {!aiEvaluation && (
                  <p className="text-[10px] text-slate-400 mt-2 text-center">
                     *数据基于 AI 实时反馈日志自动生成
                  </p>
               )}
            </div>

            {/* 4. Timeline (Key Moments) */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-4 relative">
               <h3 className="text-sm font-bold text-slate-800 mb-4 flex items-center">
                  <span className="w-1 h-4 bg-orange-500 rounded mr-2"></span>
                  关键对话时刻 (Key Moments)
               </h3>
               {/* Passed the handler to Timeline */}
               <Timeline
                  messages={data.messages}
                  onViewTranscript={() => setIsTranscriptOpen(true)}
               />
            </div>
         </div>

         {/* 5. Footer Actions */}
         <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 p-4 pb-safe shadow-[0_-4px_10px_rgba(0,0,0,0.05)] z-40 max-w-md mx-auto">
            <div className="flex gap-3">
               <Button variant="secondary" onClick={onExit} className="flex-1" icon={<List className="w-4 h-4" />}>
                  返回列表
               </Button>
               {/* Retry Button Removed */}
            </div>
         </div>

         {/* Evaluation Modal */}
         <Modal
            isOpen={isEvalModalOpen}
            onClose={() => setIsEvalModalOpen(false)}
            title="AI 智能重新评估"
            footer={
               <>
                  {isEvaluating ? (
                     <Button variant="ghost" disabled>评估中...</Button>
                  ) : hasUnsavedChanges ? (
                     <>
                        <Button variant="ghost" onClick={() => setIsEvalModalOpen(false)}>关闭 (不保存)</Button>
                        <Button
                           variant="primary"
                           onClick={handleSaveResult}
                           icon={<Save className="w-4 h-4" />}
                        >
                           保存评估结果
                        </Button>
                     </>
                  ) : (
                     <>
                        <Button variant="ghost" onClick={() => setIsEvalModalOpen(false)}>关闭</Button>
                        <Button
                           variant="primary"
                           onClick={handleReEvaluate}
                           icon={<Sparkles className="w-4 h-4" />}
                        >
                           {aiEvaluation ? '重新运行评估' : '运行评估'}
                        </Button>
                     </>
                  )}
               </>
            }
         >
            {/* ... (Keep existing Evaluation Modal Content) ... */}
            <div className="space-y-3 flex flex-col h-[70vh]">
               <div className="flex-shrink-0 space-y-3">
                  <p className="text-xs text-slate-500">
                     您可以修改下方的系统提示词 (Prompt)，让 AI 从不同的视角对本次对话进行重新打分。
                  </p>
                  <div className="relative">
                     <textarea
                        value={evalPromptTemplate}
                        onChange={(e) => setEvalPromptTemplate(e.target.value)}
                        className="w-full h-32 p-3 text-xs font-mono bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-medical-500 focus:border-transparent text-slate-700 leading-relaxed resize-none"
                        placeholder="输入评估指令..."
                     />
                     <div className="absolute bottom-2 right-2">
                        <button
                           onClick={() => setEvalPromptTemplate(DEFAULT_EVAL_PROMPT)}
                           className="text-[10px] text-slate-400 hover:text-medical-600 bg-white px-2 py-1 rounded border shadow-sm"
                        >
                           恢复默认
                        </button>
                     </div>
                  </div>
               </div>

               <div className="flex-1 min-h-0 flex flex-col">
                  <div className="text-xs font-bold text-slate-700 mb-2 mt-2 flex items-center">
                     <List className="w-3.5 h-3.5 mr-1.5 text-medical-600" />
                     执行日志 (Debug Console)
                  </div>
                  <div className="flex-1 relative border border-slate-200 rounded-lg overflow-hidden bg-slate-900">
                     <div className="absolute inset-0 overflow-y-auto">
                        <DebugConsole logs={logs} onClear={() => setLogs([])} />
                     </div>
                  </div>
               </div>
            </div>
         </Modal>

         {/* Transcript Modal */}
         <Modal
            isOpen={isTranscriptOpen}
            onClose={() => setIsTranscriptOpen(false)}
            title="完整对话记录"
            footer={
               <Button variant="primary" onClick={() => setIsTranscriptOpen(false)}>关闭</Button>
            }
         >
            <div className="flex flex-col space-y-4 h-[60vh] overflow-y-auto p-2 scroll-smooth">
               {data.messages.filter(m => m.type === 'text').length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-slate-400 text-xs">
                     <p>暂无对话记录</p>
                  </div>
               ) : (
                  data.messages.filter(m => m.type === 'text').map((msg) => (
                     <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] rounded-lg p-3 text-sm leading-relaxed shadow-sm ${msg.role === 'user'
                           ? 'bg-medical-600 text-white rounded-br-none'
                           : 'bg-slate-100 text-slate-800 rounded-bl-none border border-slate-200'
                           }`}>
                           <div className={`text-[10px] font-bold mb-1 opacity-80 ${msg.role === 'user' ? 'text-medical-100' : 'text-slate-500'}`}>
                              {msg.role === 'user' ? 'Doctor (You)' : (role?.nameCN || 'Patient')}
                           </div>
                           <div className="whitespace-pre-wrap">{msg.content}</div>
                        </div>
                     </div>
                  ))
               )}
            </div>
         </Modal>

      </div>
   );
};
