import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Code,
  Copy,
  Check,
  ChevronRight,
  Info
} from 'lucide-react';

interface PseudocodeProps {
  pseudocode: {
    language: string;
    code: string;
    annotations: { line: number; text: string }[];
    variables?: { name: string; description: string }[];
    key_operations?: string[];
    return_values?: { value: string; condition: string }[];
    flow_steps?: string[];
  };
}

const AlgorithmPseudocode: React.FC<PseudocodeProps> = ({ pseudocode }) => {
  const [copied, setCopied] = useState(false);
  const [hoveredLine, setHoveredLine] = useState<number | null>(null);
  const [showAllAnnotations, setShowAllAnnotations] = useState(false);

  const codeLines = pseudocode.code.split('\n');

  const getAnnotationForLine = (lineIndex: number) => {
    return pseudocode.annotations.find(a => a.line === lineIndex + 1);
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(pseudocode.code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const highlightSyntax = (line: string) => {
    const keywords = ['function', 'if', 'else', 'while', 'return', 'for', 'in', 'and', 'or', 'not'];
    const operators = ['==', '!=', '<=', '>=', '<', '>', '=', '+', '-', '*', '/', '%'];

    let result = line;

    keywords.forEach(keyword => {
      const regex = new RegExp(`\\b(${keyword})\\b`, 'g');
      result = result.replace(regex, `<span class="text-purple-400 font-bold">$1</span>`);
    });

    result = result.replace(/\b(\d+)\b/g, '<span class="text-orange-400">$1</span>');

    result = result.replace(/"([^"]*)"/g, '<span class="text-green-400">"$1"</span>');
    result = result.replace(/'([^']*)'/g, '<span class="text-green-400">\'$1\'</span>');

    result = result.replace(/(\w+)(\()/g, '<span class="text-cyan-400">$1</span>$2');

    result = result.replace(/(\/\/.*$|#.*$)/gm, '<span class="text-slate-500 italic">$1</span>');

    return result;
  };

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
            <Code size={24} className="text-white" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">Pseudocode</h3>
            <p className="text-slate-400 text-sm">
              Hover over any line to see its explanation
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowAllAnnotations(!showAllAnnotations)}
            className={`px-4 py-2 rounded-lg font-medium text-sm flex items-center gap-2 transition-colors ${
              showAllAnnotations
                ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            <Info size={16} />
            {showAllAnnotations ? 'Hide' : 'Show'} All Notes
          </button>
          <button
            onClick={handleCopy}
            className="px-4 py-2 rounded-lg font-medium text-sm bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white transition-colors flex items-center gap-2"
          >
            {copied ? <Check size={16} className="text-green-400" /> : <Copy size={16} />}
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden"
      >
        <div className="flex items-center justify-between px-4 py-3 bg-slate-800/50 border-b border-slate-700">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500/50"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500/50"></div>
            <div className="w-3 h-3 rounded-full bg-green-500/50"></div>
          </div>
          <span className="text-xs font-mono text-slate-500 uppercase tracking-wider">
            {pseudocode.language || 'pseudocode'}
          </span>
        </div>

        <div className="p-6 overflow-x-auto">
          <div className="font-mono text-sm">
            {codeLines.map((line, idx) => {
              const annotation = getAnnotationForLine(idx);
              const isHovered = hoveredLine === idx;
              const isEmpty = line.trim() === '';

              return (
                <div
                  key={idx}
                  className="group"
                  onMouseEnter={() => setHoveredLine(idx)}
                  onMouseLeave={() => setHoveredLine(null)}
                >
                  <div
                    className={`flex items-start transition-colors rounded ${
                      isHovered && annotation ? 'bg-cyan-500/10' : ''
                    }`}
                  >
                    <span className="w-12 text-right pr-4 text-slate-600 select-none flex-shrink-0">
                      {idx + 1}
                    </span>

                    <span
                      className={`flex-1 ${isEmpty ? 'h-6' : ''} text-slate-200`}
                      dangerouslySetInnerHTML={{ __html: highlightSyntax(line) || '&nbsp;' }}
                    />

                    {annotation && (
                      <span className={`ml-4 flex-shrink-0 transition-opacity ${
                        isHovered || showAllAnnotations ? 'opacity-100' : 'opacity-0 group-hover:opacity-50'
                      }`}>
                        <Info size={14} className="text-cyan-400" />
                      </span>
                    )}
                  </div>

                  {annotation && (isHovered || showAllAnnotations) && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="ml-12 mb-2 mt-1"
                    >
                      <div className="flex items-start gap-2 px-4 py-2 bg-cyan-500/10 border-l-2 border-cyan-500 rounded-r-lg">
                        <ChevronRight size={14} className="text-cyan-400 mt-0.5 flex-shrink-0" />
                        <span className="text-cyan-300 text-xs leading-relaxed">
                          {annotation.text}
                        </span>
                      </div>
                    </motion.div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </motion.div>

      {(pseudocode.variables || pseudocode.key_operations || pseudocode.return_values) && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="grid md:grid-cols-3 gap-4"
        >
          {pseudocode.variables && pseudocode.variables.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="text-xs font-mono text-purple-400 uppercase tracking-wider mb-2">
                Variables
              </div>
              <div className="space-y-2">
                {pseudocode.variables.map((v, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <code className="text-slate-300">{v.name}</code>
                    <span className="text-slate-500 text-xs">{v.description}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {pseudocode.key_operations && pseudocode.key_operations.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="text-xs font-mono text-green-400 uppercase tracking-wider mb-2">
                Key Operations
              </div>
              <div className="space-y-2 text-sm">
                {pseudocode.key_operations.map((op, idx) => (
                  <div key={idx} className="text-slate-300">{op}</div>
                ))}
              </div>
            </div>
          )}

          {pseudocode.return_values && pseudocode.return_values.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="text-xs font-mono text-orange-400 uppercase tracking-wider mb-2">
                Return Values
              </div>
              <div className="space-y-2">
                {pseudocode.return_values.map((rv, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <code className="text-slate-300">{rv.value}</code>
                    <span className="text-slate-500 text-xs">{rv.condition}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}

      {pseudocode.flow_steps && pseudocode.flow_steps.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 rounded-2xl p-8"
        >
          <h4 className="text-lg font-bold text-white mb-6">Algorithm Flow</h4>
          <div className="flex flex-wrap items-center gap-3 justify-center">
            {pseudocode.flow_steps.map((step, idx) => {
              const colors = [
                'bg-blue-500/20 border-blue-500/30 text-blue-300',
                'bg-purple-500/20 border-purple-500/30 text-purple-300',
                'bg-cyan-500/20 border-cyan-500/30 text-cyan-300',
                'bg-orange-500/20 border-orange-500/30 text-orange-300',
                'bg-green-500/20 border-green-500/30 text-green-300',
                'bg-pink-500/20 border-pink-500/30 text-pink-300',
              ];
              return (
                <React.Fragment key={idx}>
                  {idx > 0 && <ChevronRight size={20} className="text-slate-500" />}
                  <div className={`px-4 py-2 rounded-lg border font-medium ${colors[idx % colors.length]}`}>
                    {step}
                  </div>
                </React.Fragment>
              );
            })}
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default AlgorithmPseudocode;
