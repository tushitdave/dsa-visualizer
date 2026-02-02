import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Lightbulb,
  CheckCircle,
  Globe,
  ChevronRight,
  ChevronDown,
  AlertTriangle,
  Sparkles,
  Layers,
  Play,
  Pause
} from 'lucide-react';

interface OverviewProps {
  overview: {
    core_idea: string;
    when_to_use: string[];
    real_world_analogy: string;
  };
  visualExplanation: {
    steps: any[];
  };
  variations: any[];
  pitfalls: any[];
  proTips: string[];
}

const AlgorithmOverview: React.FC<OverviewProps> = ({
  overview,
  visualExplanation,
  variations,
  pitfalls,
  proTips
}) => {
  const [currentVisualStep, setCurrentVisualStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [expandedPitfall, setExpandedPitfall] = useState<number | null>(null);

  React.useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (isPlaying && visualExplanation.steps.length > 0) {
      interval = setInterval(() => {
        setCurrentVisualStep(prev => {
          if (prev >= visualExplanation.steps.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [isPlaying, visualExplanation.steps.length]);

  const currentStep = visualExplanation.steps[currentVisualStep];

  return (
    <div className="space-y-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-br from-cyan-900/30 to-blue-900/30 border border-cyan-500/30 rounded-2xl p-8"
      >
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 w-14 h-14 rounded-xl bg-cyan-500/20 flex items-center justify-center">
            <Lightbulb size={28} className="text-cyan-400" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-bold text-cyan-400 uppercase tracking-wider mb-3">
              Core Idea
            </h3>
            <p className="text-xl text-white font-medium leading-relaxed">
              {overview.core_idea}
            </p>
          </div>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-slate-900 border border-slate-800 rounded-2xl p-8"
      >
        <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-3">
          <CheckCircle size={24} className="text-green-400" />
          When to Use This Algorithm
        </h3>
        <div className="grid gap-3">
          {overview.when_to_use.map((item, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 + idx * 0.05 }}
              className="flex items-center gap-3 p-4 bg-slate-800/50 rounded-lg border border-slate-700/50"
            >
              <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center flex-shrink-0">
                <CheckCircle size={16} className="text-green-400" />
              </div>
              <span className="text-slate-200 font-medium">{item}</span>
            </motion.div>
          ))}
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-gradient-to-br from-purple-900/30 to-pink-900/30 border border-purple-500/30 rounded-2xl p-8"
      >
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 w-14 h-14 rounded-xl bg-purple-500/20 flex items-center justify-center">
            <Globe size={28} className="text-purple-400" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-bold text-purple-400 uppercase tracking-wider mb-3">
              Real World Analogy
            </h3>
            <p className="text-lg text-slate-200 leading-relaxed">
              {overview.real_world_analogy}
            </p>
          </div>
        </div>
      </motion.div>

      {visualExplanation.steps.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-slate-900 border border-slate-800 rounded-2xl p-8"
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-bold text-white flex items-center gap-3">
              <Play size={24} className="text-cyan-400" />
              Visual Walkthrough
            </h3>
            <div className="flex items-center gap-4">
              <span className="text-sm text-slate-400 font-mono">
                Step {currentVisualStep + 1} / {visualExplanation.steps.length}
              </span>
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className={`px-4 py-2 rounded-lg font-medium text-sm flex items-center gap-2 transition-colors ${
                  isPlaying
                    ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                    : 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                }`}
              >
                {isPlaying ? <Pause size={16} /> : <Play size={16} />}
                {isPlaying ? 'Pause' : 'Auto-Play'}
              </button>
            </div>
          </div>

          {currentStep && (
            <div className="space-y-6">
              <div className="bg-slate-800/50 rounded-xl p-6">
                <h4 className="text-lg font-bold text-white mb-2">{currentStep.title}</h4>
                <p className="text-slate-300">{currentStep.description}</p>
                {currentStep.comparison && (
                  <div className="mt-3 px-4 py-2 bg-cyan-500/10 rounded-lg inline-block">
                    <code className="text-cyan-400 font-mono">{currentStep.comparison}</code>
                  </div>
                )}
              </div>

              <div className="flex flex-wrap gap-2 items-center justify-center p-8 bg-slate-950/50 rounded-xl">
                {currentStep.array.map((val: number, idx: number) => {
                  const isLeft = idx === currentStep.left;
                  const isRight = idx === currentStep.right;
                  const isMid = idx === currentStep.mid;
                  const isFound = currentStep.found && isMid;
                  const isEliminated = currentStep.eliminated?.includes(idx);

                  return (
                    <div key={idx} className="flex flex-col items-center">
                      <motion.div
                        animate={{
                          scale: isMid ? 1.1 : 1,
                          opacity: isEliminated ? 0.3 : 1
                        }}
                        className={`
                          w-14 h-14 rounded-lg flex items-center justify-center font-mono font-bold text-lg relative
                          ${isFound
                            ? 'bg-green-500 text-white ring-4 ring-green-500/50'
                            : isMid
                            ? 'bg-cyan-500 text-slate-950 ring-4 ring-cyan-500/50'
                            : isLeft || isRight
                            ? 'bg-purple-500/50 text-white border-2 border-purple-400'
                            : isEliminated
                            ? 'bg-slate-800 text-slate-600'
                            : 'bg-slate-800 text-white border border-slate-700'
                          }
                        `}
                      >
                        {val}
                      </motion.div>
                      <span className="text-xs text-slate-500 mt-1 font-mono">{idx}</span>
                      <div className="h-6 flex items-center gap-1 mt-1">
                        {isLeft && <span className="text-xs px-2 py-0.5 rounded bg-purple-500/30 text-purple-300">L</span>}
                        {isRight && <span className="text-xs px-2 py-0.5 rounded bg-purple-500/30 text-purple-300">R</span>}
                        {isMid && <span className="text-xs px-2 py-0.5 rounded bg-cyan-500/30 text-cyan-300">M</span>}
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="flex items-center justify-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-slate-400">Target:</span>
                  <span className="px-3 py-1 bg-orange-500/20 text-orange-400 rounded font-mono font-bold">
                    {currentStep.target}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-4 h-4 rounded bg-purple-500/50 border-2 border-purple-400"></span>
                  <span className="text-slate-400">Boundaries (L/R)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-4 h-4 rounded bg-cyan-500"></span>
                  <span className="text-slate-400">Middle</span>
                </div>
              </div>

              <div className="flex items-center gap-2 justify-center">
                {visualExplanation.steps.map((_, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setCurrentVisualStep(idx);
                      setIsPlaying(false);
                    }}
                    className={`w-3 h-3 rounded-full transition-all ${
                      idx === currentVisualStep
                        ? 'bg-cyan-500 scale-125'
                        : idx < currentVisualStep
                        ? 'bg-green-500/50'
                        : 'bg-slate-700 hover:bg-slate-600'
                    }`}
                  />
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}

      {pitfalls.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-slate-900 border border-slate-800 rounded-2xl p-8"
        >
          <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-3">
            <AlertTriangle size={24} className="text-yellow-400" />
            Common Pitfalls to Avoid
          </h3>
          <div className="space-y-3">
            {pitfalls.map((pitfall, idx) => (
              <div
                key={idx}
                className="border border-slate-700 rounded-xl overflow-hidden"
              >
                <button
                  onClick={() => setExpandedPitfall(expandedPitfall === idx ? null : idx)}
                  className="w-full flex items-center justify-between p-4 bg-slate-800/50 hover:bg-slate-800 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-red-500/20 flex items-center justify-center">
                      <span className="text-red-400 font-bold">{idx + 1}</span>
                    </div>
                    <span className="text-white font-medium">{pitfall.title}</span>
                  </div>
                  <ChevronDown
                    size={20}
                    className={`text-slate-400 transition-transform ${
                      expandedPitfall === idx ? 'rotate-180' : ''
                    }`}
                  />
                </button>
                {expandedPitfall === idx && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    className="p-4 bg-slate-900/50 border-t border-slate-700"
                  >
                    <p className="text-slate-300 mb-4">{pitfall.problem}</p>
                    <div className="grid md:grid-cols-2 gap-4">
                      <div className="p-3 bg-red-500/10 rounded-lg border border-red-500/20">
                        <div className="text-xs font-mono text-red-400 mb-2">Bad Code:</div>
                        <code className="text-red-300 text-sm">{pitfall.bad_code}</code>
                      </div>
                      <div className="p-3 bg-green-500/10 rounded-lg border border-green-500/20">
                        <div className="text-xs font-mono text-green-400 mb-2">Good Code:</div>
                        <code className="text-green-300 text-sm">{pitfall.good_code}</code>
                      </div>
                    </div>
                    <p className="text-slate-400 text-sm mt-4">{pitfall.explanation}</p>
                  </motion.div>
                )}
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {proTips.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-gradient-to-br from-green-900/30 to-emerald-900/30 border border-green-500/30 rounded-2xl p-8"
        >
          <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-3">
            <Sparkles size={24} className="text-green-400" />
            Pro Tips
          </h3>
          <div className="grid gap-3">
            {proTips.map((tip, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 p-3 bg-slate-900/30 rounded-lg"
              >
                <div className="w-6 h-6 rounded-full bg-green-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-green-400 text-xs font-bold">{idx + 1}</span>
                </div>
                <span className="text-slate-200">{tip}</span>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {variations.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-slate-900 border border-slate-800 rounded-2xl p-8"
        >
          <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-3">
            <Layers size={24} className="text-blue-400" />
            Algorithm Variations
          </h3>
          <div className="grid md:grid-cols-2 gap-4">
            {variations.map((variation, idx) => (
              <div
                key={idx}
                className="p-4 bg-slate-800/50 rounded-xl border border-slate-700/50 hover:border-blue-500/30 transition-colors"
              >
                <h4 className="text-white font-bold mb-2">{variation.name}</h4>
                <p className="text-slate-400 text-sm mb-3">{variation.description}</p>
                <div className="text-xs">
                  <div className="text-slate-500 mb-1">Example:</div>
                  <div className="p-2 bg-slate-900/50 rounded font-mono text-cyan-400">
                    {variation.example.input} - {variation.example.output}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default AlgorithmOverview;
