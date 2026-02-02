import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronLeft,
  ChevronRight,
  BookOpen,
  Code,
  BarChart3,
  AlertTriangle,
  Lightbulb,
  Play,
  CheckCircle,
  XCircle,
  ArrowRight
} from 'lucide-react';
import AlgorithmOverview from './AlgorithmOverview';
import AlgorithmPseudocode from './AlgorithmPseudocode';
import AlgorithmComplexity from './AlgorithmComplexity';
import AlgorithmExercise from './AlgorithmExercise';

interface AlgorithmDeepDiveProps {
  algorithmId: string;
  algorithmName: string;
  onComplete: () => void;
  onSkip: () => void;
}

interface AlgorithmData {
  algorithm_id: string;
  name: string;
  display_name: string;
  category: string;
  tags: string[];
  overview: {
    core_idea: string;
    when_to_use: string[];
    real_world_analogy: string;
  };
  visual_explanation: {
    steps: any[];
  };
  pseudocode: {
    language: string;
    code: string;
    annotations: { line: number; text: string }[];
  };
  complexity: {
    time: {
      best: string;
      average: string;
      worst: string;
      explanation: string;
      comparison_data: { n: number; binary: number; linear: number }[];
    };
    space: {
      complexity: string;
      explanation: string;
    };
  };
  variations: any[];
  common_pitfalls: any[];
  practice_exercise: any;
  pro_tips: string[];
  related_problems: string[];
}

type TabId = 'overview' | 'pseudocode' | 'complexity' | 'exercise';

const AlgorithmDeepDive: React.FC<AlgorithmDeepDiveProps> = ({
  algorithmId,
  algorithmName,
  onComplete,
  onSkip
}) => {
  const [algorithmData, setAlgorithmData] = useState<AlgorithmData | null>(null);
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [loading, setLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exerciseCompleted, setExerciseCompleted] = useState(false);

  useEffect(() => {
    const loadAlgorithmData = async () => {
      setLoading(true);
      setError(null);

      try {
        const normalizedId = algorithmId
          .toLowerCase()
          .replace(/\s+/g, '_')
          .replace(/[^a-z0-9_]/g, '');

        const possibleFileNames = [
          normalizedId,
          normalizedId.replace(/_approach$/, ''),
          normalizedId.replace(/_optimization$/, ''),
          normalizedId.replace(/_algorithm$/, ''),
          normalizedId.replace(/_based_approach$/, ''),
          normalizedId.replace(/_based_optimization_approach$/, '_based_optimization'),
          ...(normalizedId.includes('binary') ? ['binary_search'] : []),
          ...(normalizedId.includes('stack') ? ['stack_based_optimization', 'monotonic_stack'] : []),
          ...(normalizedId.includes('two_pointer') ? ['two_pointer', 'two_pointers'] : []),
          ...(normalizedId.includes('sliding') ? ['sliding_window'] : []),
          ...(normalizedId.includes('hash') ? ['hash_map', 'hash_table'] : []),
          ...(normalizedId.includes('dfs') ? ['dfs', 'depth_first_search'] : []),
          ...(normalizedId.includes('bfs') ? ['bfs', 'breadth_first_search'] : []),
          ...(normalizedId.includes('dynamic') ? ['dynamic_programming', 'dp'] : []),
        ];

        const uniqueFileNames = [...new Set(possibleFileNames)];

        let data = null;

        for (const fileName of uniqueFileNames) {
          try {
            const response = await fetch(`/algorithms/${fileName}.json`);
            if (response.ok) {
              data = await response.json();
              console.log(`Loaded algorithm data from static file: ${fileName}.json`);
              break;
            }
          } catch {
          }
        }

        if (!data) {
          console.log(`Static file not found. Generating via LLM for: ${algorithmName}`);
          setIsGenerating(true);

          try {
            const backendResponse = await fetch('http://localhost:8000/algorithm/generate', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                algorithm_name: algorithmName,
                problem_context: ''
              }),
            });

            if (backendResponse.ok) {
              data = await backendResponse.json();
              console.log(`Generated algorithm data via LLM: ${data.algorithm_id}`);
            } else {
              const errorText = await backendResponse.text();
              console.error(`Backend generation failed: ${errorText}`);
            }
          } catch (backendError) {
            console.error('Failed to call backend for algorithm generation:', backendError);
          }
        }

        if (data) {
          setAlgorithmData(data);
        } else {
          throw new Error(`Algorithm data not found and could not be generated for: ${algorithmId}`);
        }
      } catch (err: any) {
        console.error('Failed to load algorithm data:', err);
        setError(err.message || 'Failed to load algorithm data');
      } finally {
        setLoading(false);
      }
    };

    loadAlgorithmData();
  }, [algorithmId]);

  const tabs: { id: TabId; label: string; icon: React.ReactNode }[] = [
    { id: 'overview', label: 'Overview', icon: <BookOpen size={16} /> },
    { id: 'pseudocode', label: 'Pseudocode', icon: <Code size={16} /> },
    { id: 'complexity', label: 'Complexity', icon: <BarChart3 size={16} /> },
    { id: 'exercise', label: 'Practice', icon: <Lightbulb size={16} /> }
  ];

  const handleExerciseComplete = () => {
    setExerciseCompleted(true);
  };

  if (loading) {
    return (
      <div className="flex flex-col h-full bg-slate-950 items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-4 border-cyan-500 border-t-transparent mb-6" />
        <p className={`font-mono text-lg mb-2 ${isGenerating ? 'text-purple-400' : 'text-cyan-400'}`}>
          {isGenerating ? 'Generating Algorithm Explanation...' : 'Loading algorithm details...'}
        </p>
        {isGenerating && (
          <div className="text-center max-w-md">
            <p className="text-slate-500 text-sm mb-2">
              Using AI to create a comprehensive explanation for "{algorithmName}"
            </p>
            <p className="text-slate-600 text-xs">
              This may take 10-20 seconds. The result will be cached for future use.
            </p>
          </div>
        )}
      </div>
    );
  }

  if (error || !algorithmData) {
    return (
      <div className="flex flex-col h-full bg-slate-950 items-center justify-center p-8">
        <AlertTriangle size={48} className="text-yellow-500 mb-4" />
        <h3 className="text-xl font-bold text-white mb-2">Algorithm Data Unavailable</h3>
        <p className="text-slate-400 text-center mb-4 max-w-md">
          {error || `We don't have detailed information for "${algorithmName}" yet.`}
        </p>
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 mb-6 max-w-md">
          <p className="text-slate-500 text-sm mb-2">
            <strong className="text-slate-400">Tip:</strong> Make sure the backend is running to enable automatic algorithm generation.
          </p>
          <code className="text-xs text-cyan-400 bg-slate-800 px-2 py-1 rounded">
            cd backend && uvicorn app.main:app --reload
          </code>
        </div>
        <div className="flex gap-4">
          <button
            onClick={onSkip}
            className="px-6 py-3 bg-cyan-500 hover:bg-cyan-400 text-slate-950 rounded-lg font-bold transition-colors"
          >
            Continue to Visualization
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-slate-950">
      <div className="border-b border-slate-800 bg-slate-900/50 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white shadow-lg">
              <BookOpen size={24} />
            </div>
            <div>
              <div className="text-xs font-mono text-purple-400 uppercase tracking-wider mb-1">
                Algorithm Deep Dive
              </div>
              <h2 className="text-2xl font-bold text-white">
                Understanding {algorithmData.display_name}
              </h2>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-slate-800 text-slate-400 text-xs font-mono">
              {algorithmData.category}
            </span>
            {algorithmData.tags.slice(0, 3).map((tag, idx) => (
              <span
                key={idx}
                className="px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-400 text-xs font-mono border border-cyan-500/20"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>

        <div className="flex gap-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all ${
                activeTab === tab.id
                  ? 'bg-cyan-500 text-slate-950'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white'
              }`}
            >
              {tab.icon}
              {tab.label}
              {tab.id === 'exercise' && exerciseCompleted && (
                <CheckCircle size={14} className="text-green-400" />
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-8">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="max-w-5xl mx-auto"
          >
            {activeTab === 'overview' && (
              <AlgorithmOverview
                overview={algorithmData.overview}
                visualExplanation={algorithmData.visual_explanation}
                variations={algorithmData.variations}
                pitfalls={algorithmData.common_pitfalls}
                proTips={algorithmData.pro_tips}
              />
            )}

            {activeTab === 'pseudocode' && (
              <AlgorithmPseudocode
                pseudocode={algorithmData.pseudocode}
              />
            )}

            {activeTab === 'complexity' && (
              <AlgorithmComplexity
                complexity={algorithmData.complexity}
              />
            )}

            {activeTab === 'exercise' && (
              <AlgorithmExercise
                exercise={algorithmData.practice_exercise}
                onComplete={handleExerciseComplete}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      <div className="border-t border-slate-800 bg-slate-900/50 p-6">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <button
            onClick={onSkip}
            className="px-6 py-3 rounded-lg font-bold text-sm hover:bg-slate-800 transition-colors text-slate-400"
          >
            Skip to Visualization
          </button>

          <div className="flex items-center gap-4">
            {activeTab !== 'overview' && (
              <button
                onClick={() => {
                  const currentIndex = tabs.findIndex(t => t.id === activeTab);
                  if (currentIndex > 0) {
                    setActiveTab(tabs[currentIndex - 1].id);
                  }
                }}
                className="px-4 py-2 rounded-lg font-medium text-sm bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors flex items-center gap-2"
              >
                <ChevronLeft size={16} />
                Previous
              </button>
            )}

            {activeTab !== 'exercise' ? (
              <button
                onClick={() => {
                  const currentIndex = tabs.findIndex(t => t.id === activeTab);
                  if (currentIndex < tabs.length - 1) {
                    setActiveTab(tabs[currentIndex + 1].id);
                  }
                }}
                className="px-4 py-2 rounded-lg font-medium text-sm bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30 transition-colors flex items-center gap-2 border border-cyan-500/30"
              >
                Next Section
                <ChevronRight size={16} />
              </button>
            ) : (
              <button
                onClick={onComplete}
                className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 text-slate-950 rounded-lg font-bold text-sm transition-all flex items-center gap-2 shadow-lg shadow-cyan-500/20"
              >
                <Play size={18} />
                Start Visualization
                <ArrowRight size={18} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlgorithmDeepDive;
