
import React, { useState, useEffect } from 'react';
import { Terminal, Settings, Zap, Cpu, MemoryStick, PlayCircle, Loader2, Cloud, ShieldCheck, ExternalLink, Globe, GraduationCap } from 'lucide-react';
import { ContextOption, ModelName } from '../types';

interface SidebarProps {
  onAnalyze: (problem: string, context: ContextOption[], learningMode: boolean) => void;
  isLoading: boolean;
  selectedModel: ModelName;
  onModelChange: (model: ModelName) => void;
  isBackendOnline: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({
  onAnalyze,
  isLoading,
  selectedModel,
  onModelChange,
  isBackendOnline
}) => {
  const [problem, setProblem] = useState(
    `Example 1:

Input: s = "babad"
Output: "bab"
Explanation: "aba" is also a valid answer.`
  );
  const [contexts, setContexts] = useState<ContextOption[]>([]);
  const [learningMode, setLearningMode] = useState(true);
  const [hasCloudKey, setHasCloudKey] = useState(false);

  useEffect(() => {
    const checkKey = async () => {
      if ((window as any).aistudio?.hasSelectedApiKey) {
        const hasKey = await (window as any).aistudio.hasSelectedApiKey();
        setHasCloudKey(hasKey);
      }
    };
    checkKey();
    const interval = setInterval(checkKey, 3000);
    return () => clearInterval(interval);
  }, []);

  const toggleContext = (opt: ContextOption) => {
    setContexts(prev => prev.includes(opt) ? prev.filter(c => c !== opt) : [...prev, opt]);
  };

  const handleAnalyze = () => {
    if (!problem.trim()) return;
    onAnalyze(problem, contexts, learningMode);
  };

  const handleSetupKey = async () => {
    if ((window as any).aistudio?.openSelectKey) {
      await (window as any).aistudio.openSelectKey();
      setHasCloudKey(true);
    }
  };

  const options: { label: ContextOption; icon: any; color: string }[] = [
    { label: 'Embedded System', icon: Cpu, color: 'text-orange-400' },
    { label: 'High Throughput', icon: Zap, color: 'text-yellow-400' },
    { label: 'Low Memory', icon: MemoryStick, color: 'text-blue-400' },
  ];

  const models: { id: ModelName; label: string; desc: string }[] = [
    { id: 'gemini-2.5-flash', label: 'Flash 2.5', desc: 'Fastest analysis' },
    { id: 'gemini-2.5-pro', label: 'Pro 2.5', desc: 'Deep reasoning' },
    { id: 'gemini-2.5-flash-lite-latest', label: 'Lite 2.5', desc: 'Low resource' },
  ];

  return (
    <div className="w-80 h-full border-r border-slate-800 bg-slate-900/50 flex flex-col overflow-hidden shrink-0">
      <div className="p-6 border-b border-slate-800 flex items-center gap-3 bg-slate-950/20">
        <div className="w-8 h-8 rounded-lg bg-cyan-500 flex items-center justify-center shadow-[0_0_15px_rgba(34,211,238,0.3)]">
          <Terminal className="text-slate-900" size={20} />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">AlgoInsight</h1>
          <p className="text-[10px] text-slate-500 font-mono uppercase tracking-widest">v2.6.0-stable</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-8 scrollbar-hide">
        <section className="space-y-3">
          <div className="flex items-center gap-2 text-slate-400 mb-2">
            <Globe size={14} />
            <span className="text-xs font-mono uppercase tracking-wider">Engine Status</span>
          </div>

          <div className={`p-5 rounded-xl border-2 transition-all duration-500 shadow-lg ${
            isBackendOnline
              ? 'border-green-500/50 bg-green-500/10 shadow-green-500/20'
              : 'border-cyan-500/50 bg-cyan-500/10 shadow-cyan-500/20'
          }`}>
            <div className="flex items-center justify-between mb-4">
               <div className="flex items-center gap-2">
                 {isBackendOnline ? (
                   <>
                     <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse shadow-lg shadow-green-400/50"></div>
                     <span className="text-xs font-black font-mono uppercase tracking-widest text-green-300">
                       Backend Online
                     </span>
                   </>
                 ) : (
                   <>
                     <div className="w-3 h-3 rounded-full bg-cyan-400 shadow-lg shadow-cyan-400/50"></div>
                     <span className="text-xs font-black font-mono uppercase tracking-widest text-cyan-300">
                       Cloud Mode
                     </span>
                   </>
                 )}
               </div>
               {isBackendOnline ? <ShieldCheck className="text-green-400" size={16} /> : <Cloud className="text-cyan-400" size={16} />}
            </div>

            <div className={`text-[10px] font-mono mb-3 px-2 py-1 rounded ${
              isBackendOnline
                ? 'text-green-400/80 bg-green-950/30'
                : 'text-cyan-400/80 bg-cyan-950/30'
            }`}>
              {isBackendOnline
                ? '🧠 Using 5-Agent Python Pipeline with Azure OpenAI'
                : '⚡ Using Direct Gemini API (Standalone Mode)'}
            </div>

            <div className="space-y-3">
              <div className="flex flex-col gap-1.5">
                <label className="text-[9px] uppercase font-bold text-slate-500 tracking-widest ml-1">Logic Model</label>
                <select
                  value={selectedModel}
                  onChange={(e) => onModelChange(e.target.value as ModelName)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs font-mono text-cyan-50 focus:outline-none focus:ring-1 focus:ring-cyan-500/50 appearance-none"
                >
                  {models.map(m => (
                    <option key={m.id} value={m.id}>{m.label} ({m.desc})</option>
                  ))}
                </select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-[9px] uppercase font-bold text-slate-500 tracking-widest ml-1">Experience Mode</label>
                <button
                  onClick={() => setLearningMode(!learningMode)}
                  className={`w-full p-3 rounded-lg border-2 transition-all flex items-center gap-3 ${
                    learningMode
                      ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border-cyan-500/50 text-white shadow-lg shadow-cyan-500/20'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <GraduationCap size={18} className={learningMode ? 'text-cyan-400' : 'text-slate-600'} />
                  <div className="flex-1 text-left">
                    <div className="text-xs font-bold">
                      {learningMode ? '🎓 Learning Mode' : '⚡ Quick Mode'}
                    </div>
                    <div className="text-[10px] opacity-70">
                      {learningMode ? 'Step-by-step teaching' : 'Direct visualization'}
                    </div>
                  </div>
                </button>
              </div>

              {!hasCloudKey && !isBackendOnline && (
                <button
                  onClick={handleSetupKey}
                  className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded-lg text-[10px] font-bold uppercase tracking-widest border border-cyan-500/30 transition-all flex items-center justify-center gap-2"
                >
                  Connect API Key <ExternalLink size={10} />
                </button>
              )}
            </div>
          </div>
        </section>

        <section className="space-y-4">
          <div className="flex items-center gap-2 text-slate-400 mb-2">
            <Settings size={14} />
            <span className="text-xs font-mono uppercase tracking-wider">Problem Input</span>
          </div>
          <textarea
            value={problem}
            onChange={(e) => setProblem(e.target.value)}
            placeholder="e.g., 'Explain QuickSort with an array of 8 random numbers'..."
            className="w-full h-40 bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm font-mono text-cyan-50 focus:outline-none focus:ring-1 focus:ring-cyan-500/50 resize-none transition-all placeholder:text-slate-700 shadow-inner"
          />
        </section>

        <section className="space-y-4">
          <div className="flex items-center gap-2 text-slate-400 mb-2">
            <Zap size={14} />
            <span className="text-xs font-mono uppercase tracking-wider">Contextual Toggles</span>
          </div>
          <div className="space-y-2">
            {options.map((opt) => (
              <button
                key={opt.label}
                onClick={() => toggleContext(opt.label)}
                className={`w-full flex items-center gap-3 p-3 rounded-lg border transition-all duration-200 group ${
                  contexts.includes(opt.label)
                    ? 'bg-slate-800 border-slate-600 text-white shadow-[0_0_15px_rgba(30,41,59,0.5)]'
                    : 'bg-transparent border-slate-800 text-slate-500 hover:border-slate-700 hover:text-slate-300'
                }`}
              >
                <opt.icon size={18} className={contexts.includes(opt.label) ? opt.color : 'text-slate-600'} />
                <span className="text-sm font-medium">{opt.label}</span>
              </button>
            ))}
          </div>
        </section>
      </div>

      <div className="p-6 border-t border-slate-800 bg-slate-950/50">
        <button
          onClick={handleAnalyze}
          disabled={isLoading || !problem.trim()}
          className="w-full flex items-center justify-center gap-2 bg-cyan-500 hover:bg-cyan-400 disabled:bg-slate-800 disabled:text-slate-600 text-slate-950 font-bold py-3 rounded-lg transition-all shadow-lg shadow-cyan-500/20 active:scale-95"
        >
          {isLoading ? <Loader2 className="animate-spin" size={20} /> : <PlayCircle size={20} />}
          {isLoading ? 'GENERATING...' : 'ANALYZE & VISUALIZE'}
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
