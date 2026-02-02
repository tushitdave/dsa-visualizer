import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart3,
  Clock,
  Database,
  TrendingUp,
  Minus,
  ChevronUp,
  ChevronDown
} from 'lucide-react';

interface ComplexityProps {
  complexity: {
    time: {
      best: string;
      average: string;
      worst: string;
      explanation: string;
      comparison_data: Record<string, number>[];
    };
    space: {
      complexity: string;
      explanation: string;
      variables?: string[];
    };
    algorithm_name?: string;
    best_case_desc?: string;
    average_case_desc?: string;
    worst_case_desc?: string;
    math_insight?: string;
    key_takeaway?: string;
  };
}

const AlgorithmComplexity: React.FC<ComplexityProps> = ({ complexity }) => {
  const [selectedN, setSelectedN] = useState(1000);

  const comparisonData = complexity.time.comparison_data || [];
  const selectedData = comparisonData.find(d => d.n === selectedN) || comparisonData[2] || comparisonData[0];

  // Dynamic algorithm info with fallbacks
  const algorithmName = complexity.algorithm_name || 'This Algorithm';
  const bestCaseDesc = complexity.best_case_desc || 'Optimal scenario for the algorithm';
  const avgCaseDesc = complexity.average_case_desc || 'Typical performance for random inputs';
  const worstCaseDesc = complexity.worst_case_desc || 'Maximum operations required';
  const mathInsight = complexity.math_insight;
  const keyTakeaway = complexity.key_takeaway;
  const spaceVariables = complexity.space.variables || [];

  const getComparisonKeys = () => {
    if (!selectedData) return { fast: 'binary', slow: 'linear', fastLabel: 'Optimized', slowLabel: 'Naive' };
    const keys = Object.keys(selectedData).filter(k => k !== 'n');
    if (keys.includes('binary')) return { fast: 'binary', slow: 'linear', fastLabel: 'Binary Search', slowLabel: 'Linear Search' };
    if (keys.includes('stack')) return { fast: 'stack', slow: 'bruteforce', fastLabel: 'Stack-Based', slowLabel: 'Brute Force' };
    if (keys.includes('twopointer')) return { fast: 'twopointer', slow: 'bruteforce', fastLabel: 'Two Pointer', slowLabel: 'Brute Force' };
    if (keys.includes('sliding')) return { fast: 'sliding', slow: 'bruteforce', fastLabel: 'Sliding Window', slowLabel: 'Brute Force' };
    if (keys.includes('hashmap')) return { fast: 'hashmap', slow: 'bruteforce', fastLabel: 'Hash Map', slowLabel: 'Brute Force' };
    if (keys.includes('optimized')) return { fast: 'optimized', slow: 'naive', fastLabel: 'Optimized', slowLabel: 'Naive' };
    if (keys.includes('dp')) return { fast: 'dp', slow: 'recursive', fastLabel: 'Dynamic Programming', slowLabel: 'Recursive' };
    const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1).replace(/_/g, ' ');
    return { fast: keys[0], slow: keys[1], fastLabel: capitalize(keys[0] || 'fast'), slowLabel: capitalize(keys[1] || 'slow') };
  };

  const { fast, slow, fastLabel = 'Optimized', slowLabel = 'Naive' } = getComparisonKeys();
  const fastValue = selectedData?.[fast] || 0;
  const slowValue = selectedData?.[slow] || 1;

  const maxSlow = Math.max(...comparisonData.map(d => d[slow] || 0));
  const getBarWidth = (value: number, isSlow: boolean) => {
    if (isSlow) {
      return Math.min(100, (value / maxSlow) * 100);
    }
    return Math.min(100, Math.max(5, (value / slowValue) * 100));
  };

  return (
    <div className="space-y-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid md:grid-cols-3 gap-4"
      >
        <div className="bg-gradient-to-br from-green-900/30 to-emerald-900/30 border border-green-500/30 rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
              <TrendingUp size={20} className="text-green-400" />
            </div>
            <div>
              <div className="text-xs font-mono text-green-400 uppercase tracking-wider">Best Case</div>
              <div className="text-2xl font-bold text-white font-mono">{complexity.time.best}</div>
            </div>
          </div>
          <p className="text-slate-400 text-sm">{bestCaseDesc}</p>
        </div>

        <div className="bg-gradient-to-br from-cyan-900/30 to-blue-900/30 border border-cyan-500/30 rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center">
              <Minus size={20} className="text-cyan-400" />
            </div>
            <div>
              <div className="text-xs font-mono text-cyan-400 uppercase tracking-wider">Average Case</div>
              <div className="text-2xl font-bold text-white font-mono">{complexity.time.average}</div>
            </div>
          </div>
          <p className="text-slate-400 text-sm">{avgCaseDesc}</p>
        </div>

        <div className="bg-gradient-to-br from-orange-900/30 to-red-900/30 border border-orange-500/30 rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center">
              <ChevronDown size={20} className="text-orange-400" />
            </div>
            <div>
              <div className="text-xs font-mono text-orange-400 uppercase tracking-wider">Worst Case</div>
              <div className="text-2xl font-bold text-white font-mono">{complexity.time.worst}</div>
            </div>
          </div>
          <p className="text-slate-400 text-sm">{worstCaseDesc}</p>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-slate-900 border border-slate-800 rounded-2xl p-8"
      >
        <div className="flex items-start gap-4">
          <div className="w-14 h-14 rounded-xl bg-cyan-500/20 flex items-center justify-center flex-shrink-0">
            <Clock size={28} className="text-cyan-400" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white mb-3">Why {complexity.time.average}?</h3>
            <p className="text-slate-300 leading-relaxed">{complexity.time.explanation}</p>
            {mathInsight && (
              <div className="mt-4 p-4 bg-slate-800/50 rounded-lg">
                <div className="text-xs font-mono text-slate-500 mb-2">Mathematical Insight:</div>
                <p className="text-cyan-400 font-mono whitespace-pre-line">{mathInsight}</p>
              </div>
            )}
          </div>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-slate-900 border border-slate-800 rounded-2xl p-8"
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-white flex items-center gap-3">
            <BarChart3 size={24} className="text-purple-400" />
            {fastLabel} vs {slowLabel}
          </h3>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-400">Array Size (n):</span>
            <select
              value={selectedN}
              onChange={(e) => setSelectedN(Number(e.target.value))}
              className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white font-mono focus:outline-none focus:border-cyan-500"
            >
              {comparisonData.map((d) => (
                <option key={d.n} value={d.n}>
                  {d.n.toLocaleString()}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="space-y-6">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-slate-300 font-medium">{fastLabel}</span>
              <span className="text-cyan-400 font-mono font-bold">
                ~{fastValue?.toLocaleString()} operations
              </span>
            </div>
            <div className="h-10 bg-slate-800 rounded-lg overflow-hidden relative">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${getBarWidth(fastValue, false)}%` }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
                className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg flex items-center justify-end pr-3"
              >
                <span className="text-white font-bold text-sm">{fastValue?.toLocaleString()}</span>
              </motion.div>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-slate-300 font-medium">{slowLabel}</span>
              <span className="text-orange-400 font-mono font-bold">
                ~{slowValue?.toLocaleString()} operations
              </span>
            </div>
            <div className="h-10 bg-slate-800 rounded-lg overflow-hidden relative">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${getBarWidth(slowValue, true)}%` }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
                className="h-full bg-gradient-to-r from-orange-500 to-red-500 rounded-lg flex items-center justify-end pr-3"
              >
                <span className="text-white font-bold text-sm">
                  {slowValue?.toLocaleString()}
                </span>
              </motion.div>
            </div>
          </div>
        </div>

        <div className="mt-6 p-4 bg-gradient-to-r from-green-900/30 to-emerald-900/30 border border-green-500/30 rounded-xl">
          <div className="flex items-center justify-center gap-4">
            <span className="text-green-400 font-bold text-lg">
              {fastLabel} is{' '}
              <span className="text-2xl">
                {slowValue && fastValue ? Math.round(slowValue / fastValue) : 0}x
              </span>{' '}
              faster!
            </span>
          </div>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden"
      >
        <div className="px-6 py-4 bg-slate-800/50 border-b border-slate-700">
          <h3 className="text-lg font-bold text-white">Comparison at Different Scales</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="px-6 py-3 text-left text-xs font-mono text-slate-500 uppercase tracking-wider">
                  Input Size (n)
                </th>
                <th className="px-6 py-3 text-left text-xs font-mono text-cyan-400 uppercase tracking-wider">
                  {fastLabel}
                </th>
                <th className="px-6 py-3 text-left text-xs font-mono text-orange-400 uppercase tracking-wider">
                  {slowLabel}
                </th>
                <th className="px-6 py-3 text-left text-xs font-mono text-green-400 uppercase tracking-wider">
                  Speedup
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {comparisonData.map((row, idx) => {
                const rowFast = row[fast] || 0;
                const rowSlow = row[slow] || 1;
                return (
                  <tr
                    key={idx}
                    className={`hover:bg-slate-800/50 transition-colors ${
                      row.n === selectedN ? 'bg-cyan-500/10' : ''
                    }`}
                  >
                    <td className="px-6 py-4 text-white font-mono">{row.n?.toLocaleString()}</td>
                    <td className="px-6 py-4 text-cyan-400 font-mono">{rowFast?.toLocaleString()}</td>
                    <td className="px-6 py-4 text-orange-400 font-mono">{rowSlow?.toLocaleString()}</td>
                    <td className="px-6 py-4 text-green-400 font-bold font-mono">
                      {rowFast ? Math.round(rowSlow / rowFast) : 0}x
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-gradient-to-br from-purple-900/30 to-pink-900/30 border border-purple-500/30 rounded-2xl p-8"
      >
        <div className="flex items-start gap-4">
          <div className="w-14 h-14 rounded-xl bg-purple-500/20 flex items-center justify-center flex-shrink-0">
            <Database size={28} className="text-purple-400" />
          </div>
          <div>
            <div className="flex items-center gap-3 mb-3">
              <h3 className="text-lg font-bold text-white">Space Complexity</h3>
              <span className="px-3 py-1 bg-purple-500/20 rounded-lg text-purple-400 font-mono font-bold">
                {complexity.space.complexity}
              </span>
            </div>
            <p className="text-slate-300 leading-relaxed">{complexity.space.explanation}</p>
            {spaceVariables.length > 0 && (
              <div className="mt-4 flex gap-4">
                <div className="px-4 py-2 bg-slate-900/50 rounded-lg">
                  <div className="text-xs text-slate-500 mb-1">Variables Used</div>
                  <div className="flex flex-wrap gap-2">
                    {spaceVariables.map((v, i) => (
                      <code key={i} className="px-2 py-1 bg-purple-500/20 rounded text-purple-400 text-sm">{v}</code>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </motion.div>

      {keyTakeaway && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/30 rounded-2xl p-6"
        >
          <div className="text-center">
            <div className="text-xs font-mono text-cyan-400 uppercase tracking-wider mb-2">
              Key Takeaway
            </div>
            <p className="text-xl text-white font-medium">{keyTakeaway}</p>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default AlgorithmComplexity;
