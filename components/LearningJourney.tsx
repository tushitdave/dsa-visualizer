import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, CheckCircle, BookOpen, Search, Lightbulb, ArrowRight } from 'lucide-react';

interface Phase {
  phase: string;
  phase_number: number;
  phase_title: string;
  content: any;
}

interface LearningJourneyProps {
  phases: Phase[];
  totalPhases: number;
  onComplete: () => void;
  onLearnAlgorithm?: (algorithmName: string) => void;
}

const LearningJourney: React.FC<LearningJourneyProps> = ({ phases, totalPhases, onComplete, onLearnAlgorithm }) => {
  const [currentPhaseIndex, setCurrentPhaseIndex] = useState(0);

  const currentPhase = phases[currentPhaseIndex];

  if (!currentPhase) {
    console.error('[LearningJourney] currentPhase is undefined!', {
      currentPhaseIndex,
      phasesLength: phases.length,
      phases
    });
    return (
      <div className="flex items-center justify-center h-full text-red-400">
        <div className="text-center">
          <p className="font-bold text-lg mb-2">Error: Phase data missing</p>
          <p className="text-sm">Phase index: {currentPhaseIndex}, Total phases: {phases.length}</p>
        </div>
      </div>
    );
  }

  const handleNext = () => {
    console.log('[LearningJourney] Next button clicked', {
      currentPhaseIndex,
      totalPhases: phases.length
    });

    if (currentPhaseIndex < phases.length - 1) {
      setCurrentPhaseIndex(currentPhaseIndex + 1);
      console.log('[LearningJourney] Moving to next phase:', currentPhaseIndex + 1);
    } else {
      console.log('[LearningJourney] Last phase reached, calling onComplete()');
      onComplete();
    }
  };

  const handlePrevious = () => {
    if (currentPhaseIndex > 0) {
      setCurrentPhaseIndex(currentPhaseIndex - 1);
    }
  };

  const getPhaseIcon = (phaseType: string) => {
    switch (phaseType) {
      case 'understand_problem':
        return <BookOpen size={24} />;
      case 'analyze_input':
        return <Search size={24} />;
      case 'explore_approaches':
        return <Lightbulb size={24} />;
      default:
        return <BookOpen size={24} />;
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-950">
      <div className="border-b border-slate-800 bg-slate-900/50 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white flex items-center gap-3">
            Learning Journey
          </h2>
          <span className="text-sm font-mono text-slate-500">
            Phase {currentPhaseIndex + 1} of {totalPhases}
          </span>
        </div>

        <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-cyan-500 to-blue-500"
            initial={{ width: 0 }}
            animate={{ width: `${((currentPhaseIndex + 1) / totalPhases) * 100}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>

        <div className="flex items-center gap-4 mt-4">
          {phases.map((phase, idx) => (
            <div
              key={idx}
              className={`flex items-center gap-2 text-xs ${
                idx === currentPhaseIndex
                  ? 'text-cyan-400 font-bold'
                  : idx < currentPhaseIndex
                  ? 'text-green-400'
                  : 'text-slate-600'
              }`}
            >
              {idx < currentPhaseIndex ? (
                <CheckCircle size={16} />
              ) : (
                <div
                  className={`w-4 h-4 rounded-full border-2 ${
                    idx === currentPhaseIndex ? 'border-cyan-400 bg-cyan-400/20' : 'border-slate-700'
                  }`}
                />
              )}
              <span className="hidden md:inline">{phase.phase_title.split(':')[0]}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-8">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentPhaseIndex}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="max-w-4xl mx-auto space-y-8"
          >
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center text-white shadow-lg shadow-cyan-500/20">
                {getPhaseIcon(currentPhase.phase)}
              </div>
              <div className="flex-1">
                <div className="text-xs font-mono text-cyan-400 uppercase tracking-wider mb-1">
                  Phase {currentPhase.phase_number}
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">{currentPhase.phase_title}</h3>
              </div>
            </div>

            {currentPhase.phase === 'understand_problem' && (
              <PhaseUnderstand content={currentPhase.content} />
            )}
            {currentPhase.phase === 'analyze_input' && (
              <PhaseAnalyze content={currentPhase.content} />
            )}
            {currentPhase.phase === 'explore_approaches' && (
              <PhaseExplore
                content={currentPhase.content}
                onLearnAlgorithm={onLearnAlgorithm}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      <div className="border-t border-slate-800 bg-slate-900/50 p-6">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <button
            onClick={handlePrevious}
            disabled={currentPhaseIndex === 0}
            className="px-6 py-3 rounded-lg font-bold text-sm disabled:opacity-30 disabled:cursor-not-allowed hover:bg-slate-800 transition-colors text-slate-300"
          >
            Previous
          </button>

          <div className="text-center">
            <div className="text-xs text-slate-500 mb-1">Next up</div>
            <div className="text-sm font-bold text-white">
              {currentPhaseIndex < phases.length - 1
                ? phases[currentPhaseIndex + 1].phase_title
                : 'Start Visualization'}
            </div>
          </div>

          <button
            onClick={handleNext}
            className="px-6 py-3 bg-cyan-500 hover:bg-cyan-400 text-slate-950 rounded-lg font-bold text-sm transition-all flex items-center gap-2 shadow-lg shadow-cyan-500/20"
          >
            {currentPhaseIndex < phases.length - 1 ? 'Next Phase' : 'Start Visualization'}
            <ChevronRight size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};

const PhaseUnderstand: React.FC<{ content: any }> = ({ content }) => (
  <div className="space-y-6">
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
      <div className="text-xs font-mono text-slate-500 uppercase tracking-wider mb-3">
        Problem Statement
      </div>
      <p className="text-slate-300 leading-relaxed">{safeRender(content.problem_statement)}</p>
    </div>

    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
      <div className="text-xs font-mono text-cyan-400 uppercase tracking-wider mb-4">
        Let's break this down:
      </div>

      <div className="grid gap-4">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center text-green-400 text-sm font-bold">
            +
          </div>
          <div>
            <div className="text-xs font-mono text-slate-500 mb-1">Objective</div>
            <div className="text-white font-medium">{safeRender(content.breakdown?.objective)}</div>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center text-blue-400 text-sm font-bold">
            +
          </div>
          <div>
            <div className="text-xs font-mono text-slate-500 mb-1">Input</div>
            <div className="text-white font-medium">{safeRender(content.breakdown?.input)}</div>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center text-purple-400 text-sm font-bold">
            +
          </div>
          <div>
            <div className="text-xs font-mono text-slate-500 mb-1">Output</div>
            <div className="text-white font-medium">{safeRender(content.breakdown?.output)}</div>
          </div>
        </div>

        {content.breakdown?.constraints && Array.isArray(content.breakdown.constraints) && content.breakdown.constraints.length > 0 && (
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-orange-500/20 flex items-center justify-center text-orange-400 text-sm font-bold">
              !
            </div>
            <div>
              <div className="text-xs font-mono text-slate-500 mb-1">Constraints</div>
              <div className="space-y-1">
                {content.breakdown.constraints.map((c: any, i: number) => (
                  <div key={i} className="text-white font-medium">
                    - {safeRender(c)}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>

    {content.key_insights && Array.isArray(content.key_insights) && content.key_insights.length > 0 && (
      <div className="bg-gradient-to-r from-cyan-900/40 to-blue-900/40 border border-cyan-500/30 rounded-xl p-6">
        <div className="text-xs font-mono text-cyan-400 uppercase tracking-wider mb-4 flex items-center gap-2">
          What does this tell us?
        </div>
        <div className="space-y-3">
          {content.key_insights.map((insight: any, i: number) => (
            <div key={i} className="flex items-start gap-3">
              <ArrowRight size={16} className="text-cyan-400 mt-1 flex-shrink-0" />
              <p className="text-white font-medium leading-relaxed">{safeRender(insight)}</p>
            </div>
          ))}
        </div>
      </div>
    )}
  </div>
);

// Safe render helper - converts any value to a displayable string
const safeRender = (val: any, maxLen = 500): string => {
  try {
    if (val === null || val === undefined) return '';
    if (typeof val === 'string') {
      return val.length > maxLen ? val.slice(0, maxLen) + '...' : val;
    }
    if (typeof val === 'number' || typeof val === 'boolean') {
      return String(val);
    }
    if (Array.isArray(val)) {
      const str = '[' + val.map(v => safeRender(v, 50)).join(', ') + ']';
      return str.length > maxLen ? str.slice(0, maxLen) + '...' : str;
    }
    if (typeof val === 'object') {
      const str = JSON.stringify(val, null, 0);
      return str.length > maxLen ? str.slice(0, maxLen) + '...' : str;
    }
    return String(val);
  } catch {
    return '[Error displaying value]';
  }
};

const renderValue = (val: any): string => {
  return safeRender(val, 100);
};

const PhaseAnalyze: React.FC<{ content: any }> = ({ content }) => (
  <div className="space-y-6">
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
      <div className="text-xs font-mono text-slate-500 uppercase tracking-wider mb-3">
        Input Data Structure
      </div>
      <div className="flex items-center gap-4">
        <div className="px-4 py-2 bg-cyan-500/20 border border-cyan-500/30 rounded-lg">
          <span className="text-cyan-300 font-mono font-bold uppercase">
            {safeRender(content.data_structure_type)}
          </span>
        </div>
      </div>
    </div>

    {content.sample_input && content.sample_input.values && Array.isArray(content.sample_input.values) && content.sample_input.values.length > 0 && (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="text-xs font-mono text-slate-500 uppercase tracking-wider mb-4">
          Visual Representation
        </div>
        <div className="flex flex-wrap gap-2 items-center justify-center p-6 bg-slate-950/50 rounded-lg max-h-64 overflow-auto">
          {content.sample_input.values.slice(0, 50).map((val: any, idx: number) => (
            <div
              key={idx}
              className="min-w-14 h-14 px-2 rounded-lg bg-slate-800 border-2 border-cyan-500/30 flex items-center justify-center font-mono font-bold text-white text-sm relative group"
            >
              {renderValue(val)}
              <span className="absolute -bottom-1 -right-1 w-5 h-5 bg-slate-900 border border-slate-700 rounded text-xs flex items-center justify-center text-slate-500">
                {idx}
              </span>
            </div>
          ))}
          {content.sample_input.values.length > 50 && (
            <div className="text-slate-500 font-mono text-xs">+{content.sample_input.values.length - 50} more</div>
          )}
        </div>
      </div>
    )}

    {content.properties && Array.isArray(content.properties) && content.properties.length > 0 && (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-3">
        <div className="text-xs font-mono text-cyan-400 uppercase tracking-wider mb-4">
          Properties we discovered:
        </div>
        {content.properties.map((prop: any, i: number) => (
          <div key={i} className="flex items-start gap-3">
            <CheckCircle size={18} className="text-green-400 mt-0.5 flex-shrink-0" />
            <p className="text-white font-medium">{safeRender(prop)}</p>
          </div>
        ))}
      </div>
    )}

    {content.why_properties_matter && Array.isArray(content.why_properties_matter) && content.why_properties_matter.length > 0 && (
      <div className="bg-gradient-to-r from-cyan-900/40 to-blue-900/40 border border-cyan-500/30 rounded-xl p-6">
        <div className="text-xs font-mono text-cyan-400 uppercase tracking-wider mb-4">
          Why this matters:
        </div>
        <div className="space-y-3">
          {content.why_properties_matter.map((reason: any, i: number) => (
            <div key={i} className="flex items-start gap-3">
              <ArrowRight size={16} className="text-cyan-400 mt-1 flex-shrink-0" />
              <p className="text-white font-medium leading-relaxed">{safeRender(reason)}</p>
            </div>
          ))}
        </div>
      </div>
    )}
  </div>
);

const PhaseExplore: React.FC<{ content: any; onLearnAlgorithm?: (name: string) => void }> = ({ content, onLearnAlgorithm }) => (
  <div className="space-y-6">
    <div className="text-lg font-bold text-white mb-6">
      Let's think: How can we solve this?
    </div>

    {content.approaches && Array.isArray(content.approaches) && content.approaches.map((approach: any, idx: number) => (
      <div
        key={idx}
        className={`border-2 rounded-xl p-6 ${
          approach.meets_constraints
            ? 'border-green-500/50 bg-green-500/5'
            : 'border-red-500/30 bg-red-500/5'
        }`}
      >
        <div className="flex items-start justify-between mb-4">
          <div>
            <h4 className="text-lg font-bold text-white mb-1">
              Approach {idx + 1}: {safeRender(approach.name)}
              {approach.meets_constraints && ' *'}
            </h4>
            <p className="text-slate-400 text-sm">{safeRender(approach.description)}</p>
          </div>
          <div className="text-4xl">
            {approach.meets_constraints ? '+' : '-'}
          </div>
        </div>

        <div className="flex gap-4 mb-4">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-slate-500">Time:</span>
            <code className="px-2 py-1 bg-slate-800 rounded font-mono text-cyan-400">
              {safeRender(approach.complexity?.time)}
            </code>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-slate-500">Space:</span>
            <code className="px-2 py-1 bg-slate-800 rounded font-mono text-purple-400">
              {safeRender(approach.complexity?.space)}
            </code>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {approach.pros && Array.isArray(approach.pros) && approach.pros.length > 0 && (
            <div>
              <div className="text-xs font-mono text-green-400 mb-2">Pros:</div>
              <ul className="space-y-1">
                {approach.pros.map((pro: any, i: number) => (
                  <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                    <span className="text-green-400">+</span>
                    {safeRender(pro)}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {approach.cons && Array.isArray(approach.cons) && approach.cons.length > 0 && (
            <div>
              <div className="text-xs font-mono text-red-400 mb-2">Cons:</div>
              <ul className="space-y-1">
                {approach.cons.map((con: any, i: number) => (
                  <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                    <span className="text-red-400">-</span>
                    {safeRender(con)}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    ))}

    {content.recommended && (
      <div className="bg-gradient-to-r from-green-900/40 to-emerald-900/40 border-2 border-green-500/50 rounded-xl p-6">
        <div className="text-xs font-mono text-green-400 uppercase tracking-wider mb-4 flex items-center gap-2">
          * Recommended Approach
        </div>
        <h4 className="text-xl font-bold text-white mb-3">{safeRender(content.recommended.approach_name)}</h4>
        <p className="text-slate-300 mb-4">{safeRender(content.recommended.reason)}</p>
        {content.recommended.key_insight && (
          <div className="bg-slate-900/50 border border-green-500/30 rounded-lg p-4 mb-4">
            <div className="text-xs font-mono text-green-400 mb-2">Key Insight:</div>
            <p className="text-white font-medium">{safeRender(content.recommended.key_insight)}</p>
          </div>
        )}

        {onLearnAlgorithm && content.recommended.approach_name && (
          <div className="mt-6 pt-6 border-t border-green-500/30">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-400 mb-1">Want to understand this algorithm first?</div>
                <div className="text-xs text-slate-500">Deep dive into how {safeRender(content.recommended.approach_name)} works</div>
              </div>
              <button
                onClick={() => onLearnAlgorithm(String(content.recommended.approach_name || 'Algorithm'))}
                className="px-5 py-3 bg-purple-500 hover:bg-purple-400 text-white rounded-lg font-bold text-sm transition-all flex items-center gap-2 shadow-lg shadow-purple-500/20"
              >
                Learn {safeRender(content.recommended.approach_name)} First
              </button>
            </div>
          </div>
        )}
      </div>
    )}
  </div>
);

export default LearningJourney;
