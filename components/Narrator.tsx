
import React, { useState, useEffect } from 'react';
import { BookOpen, HelpCircle, CheckCircle2, XCircle, Info, ChevronRight, ChevronDown, Activity, X, Zap } from 'lucide-react';
import { Frame, Quiz } from '../types';
import { motion, AnimatePresence } from 'framer-motion';

// Support both old simple format and new rich format
interface SimpleComplexity {
  time: string;
  space: string;
}

interface RichComplexity {
  algorithm_name?: string;
  time: {
    best: string;
    average: string;
    worst: string;
    explanation: string;
    comparison_data?: Record<string, number>[];
  };
  space: {
    complexity: string;
    explanation: string;
    variables?: string[];
  };
  best_case_desc?: string;
  average_case_desc?: string;
  worst_case_desc?: string;
  math_insight?: string;
  key_takeaway?: string;
}

type ComplexityProp = SimpleComplexity | RichComplexity;

interface NarratorProps {
  frame: Frame;
  complexity?: ComplexityProp;
  strategy?: string;
  strategy_details?: string;
  onQuizCorrect: () => void;
  onSkipQuiz: () => void;
}

const Narrator: React.FC<NarratorProps> = ({
  frame,
  complexity,
  strategy,
  strategy_details,
  onQuizCorrect,
  onSkipQuiz
}) => {
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [isResolved, setIsResolved] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [showStrategyBrief, setShowStrategyBrief] = useState(false);

  useEffect(() => {
    setSelectedOption(null);
    setIsResolved(false);
  }, [frame.step_id]);

  const handleOptionClick = (idx: number) => {
    if (isResolved) return;
    setSelectedOption(idx);
    if (frame.quiz && idx === frame.quiz.correct) {
      setIsResolved(true);
      onQuizCorrect();
    }
  };

  // Extract complexity values - support both old and new formats
  const getComplexityDisplay = () => {
    if (!complexity) return { time: 'N/A', space: 'N/A' };

    // Check if it's the new rich format
    if (typeof complexity.time === 'object' && complexity.time !== null) {
      const richComplexity = complexity as RichComplexity;
      return {
        time: richComplexity.time.average || richComplexity.time.worst || 'N/A',
        space: richComplexity.space?.complexity || 'N/A'
      };
    }

    // Old simple format
    const simpleComplexity = complexity as SimpleComplexity;
    return {
      time: simpleComplexity.time || 'N/A',
      space: simpleComplexity.space || 'N/A'
    };
  };

  const safeComplexity = getComplexityDisplay();

  return (
    <div className="w-96 h-full border-l border-slate-800 bg-slate-900/40 flex flex-col shrink-0 relative shadow-2xl z-20">
      <div className="p-6 border-b border-slate-800 bg-slate-950/40 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2 text-cyan-400">
            <BookOpen size={16} />
            <span className="text-[10px] font-black font-mono uppercase tracking-[0.3em]">Execution Logs</span>
          </div>
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20 text-[9px] font-bold text-cyan-400">
            <Zap size={10} /> LIVE
          </div>
        </div>

        {strategy && (
          <div className="mb-6 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <button
              onClick={() => setShowStrategyBrief(!showStrategyBrief)}
              className="w-full p-4 flex items-center justify-between hover:bg-slate-800/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <Info size={14} className="text-cyan-400" />
                <div className="text-left">
                  <span className="block text-[9px] text-slate-500 font-mono uppercase tracking-widest mb-0.5">Methodology</span>
                  <h4 className="text-sm font-bold text-white tracking-tight">{strategy}</h4>
                </div>
              </div>
              <ChevronDown
                size={16}
                className={`text-cyan-400 transition-transform ${showStrategyBrief ? 'rotate-180' : ''}`}
              />
            </button>
            <AnimatePresence>
              {showStrategyBrief && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="border-t border-slate-800"
                >
                  <div className="p-4 text-xs text-slate-300 leading-relaxed">
                    {strategy_details || 'Detailed strategy information will appear here.'}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/50">
            <span className="block text-[8px] text-slate-500 font-mono uppercase tracking-widest mb-1">Time Efficiency</span>
            <span className="text-xs font-mono font-bold text-cyan-400">{safeComplexity.time}</span>
          </div>
          <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800/50">
            <span className="block text-[8px] text-slate-500 font-mono uppercase tracking-widest mb-1">Memory Usage</span>
            <span className="text-xs font-mono font-bold text-fuchsia-400">{safeComplexity.space}</span>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-8 scrollbar-hide">
        <section className="relative">
          <div className="absolute -left-3 top-0 bottom-0 w-0.5 bg-gradient-to-b from-cyan-500/50 to-transparent"></div>
          <p className="text-slate-300 leading-relaxed text-sm font-medium selection:bg-cyan-500/30">
            {frame.commentary}
          </p>
        </section>

        {frame.quiz && (
          <section className="p-5 rounded-2xl border-2 border-fuchsia-500/20 bg-fuchsia-500/5 space-y-5 shadow-[0_0_30px_rgba(217,70,239,0.05)]">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 text-fuchsia-400">
                <HelpCircle size={18} />
                <span className="text-[10px] font-black uppercase tracking-[0.2em]">Logic Verify</span>
              </div>
              {!isResolved && (
                <button
                  onClick={onSkipQuiz}
                  className="text-[9px] font-mono text-slate-500 hover:text-cyan-400 transition-colors uppercase tracking-widest flex items-center gap-1"
                >
                  Bypass <ChevronRight size={10} />
                </button>
              )}
            </div>
            <p className="text-sm font-bold text-white leading-snug">{frame.quiz.question}</p>
            <div className="space-y-2">
              {frame.quiz.options.map((opt, idx) => {
                const isSelected = selectedOption === idx;
                const isCorrect = idx === frame.quiz?.correct;
                let borderClass = 'border-slate-800 hover:border-slate-700';
                let bgClass = 'bg-slate-900/40';
                let textClass = 'text-slate-400';

                if (isSelected) {
                  if (isCorrect) {
                    borderClass = 'border-green-500 shadow-[0_0_15px_rgba(34,197,94,0.3)]';
                    bgClass = 'bg-green-500/20';
                    textClass = 'text-green-300 font-bold';
                  } else {
                    borderClass = 'border-red-500 shadow-[0_0_15px_rgba(239,68,68,0.3)]';
                    bgClass = 'bg-red-500/20';
                    textClass = 'text-red-300 font-bold';
                  }
                } else if (isResolved && isCorrect) {
                    borderClass = 'border-green-500/40';
                    textClass = 'text-green-500/60';
                }

                return (
                  <button
                    key={idx}
                    disabled={isResolved}
                    onClick={() => handleOptionClick(idx)}
                    className={`w-full text-left p-3 rounded-xl border-2 text-xs transition-all flex items-center justify-between group ${borderClass} ${bgClass} ${textClass}`}
                  >
                    <span>{opt}</span>
                    {isSelected && isCorrect && <CheckCircle2 size={16} className="shrink-0" />}
                    {isSelected && !isCorrect && <XCircle size={16} className="shrink-0" />}
                  </button>
                );
              })}
            </div>
          </section>
        )}
      </div>

      <AnimatePresence>
        {showDetails && (
          <motion.div
            initial={{ opacity: 0, x: '100%' }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="absolute inset-0 bg-slate-950 z-50 flex flex-col"
          >
            <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
              <div className="flex items-center gap-2 text-cyan-400 font-mono text-[10px] font-black uppercase tracking-[0.3em]">
                <Info size={14} />
                Detailed Specs
              </div>
              <button
                onClick={() => setShowDetails(false)}
                className="w-8 h-8 rounded-full flex items-center justify-center hover:bg-slate-800 transition-colors"
              >
                <X size={20} className="text-slate-500 hover:text-white" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-8 space-y-8 scrollbar-hide">
              <div className="space-y-4">
                <h3 className="text-2xl font-black text-white tracking-tighter leading-none">{strategy || 'Algorithm Brain'}</h3>
                <div className="h-1.5 w-16 bg-cyan-500 rounded-full shadow-[0_0_10px_rgba(34,211,238,0.8)]"></div>
              </div>
              <div className="text-slate-300 text-sm leading-relaxed font-medium space-y-6">
                {strategy_details ? (
                  strategy_details.split('\n').map((para, i) => (
                    <p key={i} className="first-letter:text-2xl first-letter:font-bold first-letter:text-cyan-400 first-letter:mr-1">{para}</p>
                  ))
                ) : (
                  <p>System definition pending. The current trace represents a high-efficiency implementation of common DSA patterns tailored to the problem input.</p>
                )}
              </div>

              <div className="pt-8 border-t border-slate-900">
                <div className="grid grid-cols-2 gap-4">
                   <div className="space-y-1">
                      <span className="text-[9px] font-mono text-slate-600 uppercase tracking-widest">Worst Case</span>
                      <p className="text-cyan-400 font-bold">{safeComplexity.time}</p>
                   </div>
                   <div className="space-y-1">
                      <span className="text-[9px] font-mono text-slate-600 uppercase tracking-widest">Auxiliary Space</span>
                      <p className="text-fuchsia-400 font-bold">{safeComplexity.space}</p>
                   </div>
                </div>
              </div>
            </div>
            <div className="p-6 bg-slate-900/80 border-t border-slate-800">
               <button
                onClick={() => setShowDetails(false)}
                className="w-full py-4 bg-cyan-500 hover:bg-cyan-400 text-slate-950 rounded-xl text-xs font-black uppercase tracking-[0.2em] transition-all shadow-xl shadow-cyan-500/20 active:scale-[0.98]"
               >
                 Close Briefing
               </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default Narrator;
