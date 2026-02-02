
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { State } from '../types';
import { HelpCircle, Layers, Cpu, Hash } from 'lucide-react';

interface VisualizerCanvasProps {
  state: State;
  isBlockedByQuiz?: boolean;
  commentary?: string;
  stepId?: number;
}

const VisualizerCanvas: React.FC<VisualizerCanvasProps> = ({ state, isBlockedByQuiz, commentary, stepId }) => {
  // Safe key generation - handles objects, arrays, and primitives
  const getStableKey = (containerName: string, val: any, idx: number) => {
    let valStr: string;
    try {
      if (val === null || val === undefined) {
        valStr = 'null';
      } else if (typeof val === 'object') {
        valStr = JSON.stringify(val).slice(0, 50); // Limit length for performance
      } else {
        valStr = String(val);
      }
    } catch {
      valStr = 'unknown';
    }
    return `el-${containerName}-${idx}-${valStr}`;
  };

  // Safe value to string conversion for display
  const safeStringify = (val: any, maxLen = 100, depth = 0): string => {
    try {
      if (depth > 5) return '...'; // Prevent infinite recursion
      if (val === null || val === undefined) return 'null';
      if (typeof val === 'string') {
        return val.length > maxLen ? val.slice(0, maxLen) + '...' : val;
      }
      if (typeof val === 'number') {
        if (!isFinite(val)) return String(val);
        return String(val);
      }
      if (typeof val === 'boolean') return String(val);
      if (Array.isArray(val)) {
        if (val.length > 20) {
          const preview = val.slice(0, 5).map(v => safeStringify(v, 20, depth + 1)).join(', ');
          return `[${preview}, ... +${val.length - 5} more]`;
        }
        return '[' + val.map(v => safeStringify(v, 20, depth + 1)).join(', ') + ']';
      }
      if (typeof val === 'object') {
        const keys = Object.keys(val);
        if (keys.length > 10) {
          return `{${keys.length} keys}`;
        }
        const str = JSON.stringify(val);
        return str.length > maxLen ? str.slice(0, maxLen) + '...' : str;
      }
      return String(val);
    } catch {
      return '[Error]';
    }
  };

  // Check if data is too large to render safely
  const isDataTooLarge = (data: any): boolean => {
    try {
      if (Array.isArray(data)) {
        if (data.length > 500) return true;
        if (Array.isArray(data[0]) && data.length * data[0].length > 2500) return true;
      }
      if (typeof data === 'object' && data !== null) {
        if (Object.keys(data).length > 100) return true;
      }
      return false;
    } catch {
      return true;
    }
  };

  const isMatrix = (data: any): boolean => {
    if (!Array.isArray(data) || data.length === 0) return false;
    if (!Array.isArray(data[0])) return false;
    const firstRowLength = data[0].length;
    return data.every((row: any) => Array.isArray(row) && row.length === firstRowLength);
  };

  const renderMatrix = (name: string, data: any[][], highlights: string[]) => {
    const isStructureHighlighted = highlights.includes(name);
    const rows = data.length;
    const cols = data[0]?.length || 0;

    return (
      <div className="flex flex-col items-center gap-6 w-full">
        <div className="flex items-center gap-3 px-6 py-3 bg-slate-900/60 border border-slate-800/50 rounded-xl">
          <Cpu size={14} className={isStructureHighlighted ? 'text-cyan-400' : 'text-slate-600'} />
          <h3 className={`text-xs font-mono uppercase tracking-[0.4em] font-black ${
            isStructureHighlighted ? 'text-cyan-400' : 'text-slate-500'
          }`}>
            {name}
            <span className="ml-2 text-slate-600 normal-case tracking-normal">
              [{rows}×{cols}]
            </span>
          </h3>
        </div>
        <div className={`p-6 bg-slate-950/40 border rounded-2xl backdrop-blur-sm transition-all duration-500 ${
          isStructureHighlighted ? 'border-cyan-500/50 shadow-[0_0_30px_rgba(34,211,238,0.15)]' : 'border-slate-800/30'
        }`}>
          <div className="flex flex-col gap-1">
            {data.map((row, rowIdx) => (
              <div key={`row-${rowIdx}`} className="flex gap-1 items-center">
                <span className="w-6 text-[10px] font-mono text-slate-600 text-right mr-2">{rowIdx}</span>
                {row.map((cell, colIdx) => {
                  const cellKey = `${name}[${rowIdx}][${colIdx}]`;
                  const rowKey = `${name}[${rowIdx}]`;
                  const isElemHighlighted =
                    highlights.includes(cellKey) ||
                    highlights.includes(rowKey) ||
                    isStructureHighlighted;

                  const cellValue = cell === null || cell === undefined ? '·' : String(cell);
                  const isZero = cellValue === '0' || cellValue === 'false';
                  const isOne = cellValue === '1' || cellValue === 'true';

                  return (
                    <motion.div
                      key={`${name}-${rowIdx}-${colIdx}`}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className={`w-10 h-10 flex items-center justify-center font-mono text-sm font-bold border transition-all duration-300 rounded-lg
                        ${isElemHighlighted
                          ? 'bg-cyan-500/30 border-cyan-400 text-white shadow-[0_0_15px_rgba(34,211,238,0.5)] z-10'
                          : isOne
                            ? 'bg-emerald-900/40 border-emerald-700/50 text-emerald-400'
                            : isZero
                              ? 'bg-slate-900/60 border-slate-800 text-slate-600'
                              : 'bg-slate-900/90 border-slate-800 text-slate-400'
                        }`}
                    >
                      {cellValue}
                    </motion.div>
                  );
                })}
              </div>
            ))}
            <div className="flex gap-1 mt-1 ml-8">
              {data[0]?.map((_, colIdx) => (
                <span key={`col-label-${colIdx}`} className="w-10 text-center text-[10px] font-mono text-slate-600">
                  {colIdx}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderHeap = (name: string, data: any, highlights: string[]) => {
    const items = Array.isArray(data) ? data : (data?.values || data?.items || []);
    const isStructureHighlighted = highlights.includes(name);

    const renderValue = (val: any): string => {
      if (val === null || val === undefined) return 'null';
      if (typeof val === 'string' || typeof val === 'number' || typeof val === 'boolean') {
        return String(val);
      }
      if (Array.isArray(val)) {
        return '[' + val.map(renderValue).join(',') + ']';
      }
      if (typeof val === 'object') {
        return JSON.stringify(val);
      }
      return String(val);
    };

    return (
      <div className="flex flex-col items-center gap-6">
        <div className="flex items-center gap-3 px-6 py-3 bg-slate-900/60 border border-slate-800/50 rounded-xl">
          <Layers size={14} className={isStructureHighlighted ? 'text-cyan-400' : 'text-slate-600'} />
          <h3 className={`text-xs font-mono uppercase tracking-[0.4em] font-black ${
            isStructureHighlighted ? 'text-cyan-400' : 'text-slate-500'
          }`}>
            {name}
          </h3>
        </div>
        <div className={`flex flex-col items-center gap-6 p-8 rounded-3xl border transition-all duration-700 ${
          isStructureHighlighted
            ? 'border-cyan-400 bg-slate-900/60 shadow-[0_0_50px_rgba(34,211,238,0.2)]'
            : 'border-slate-800/50 bg-slate-900/20'
        }`}>
          <div className="flex flex-wrap justify-center gap-4 max-w-2xl">
            <AnimatePresence mode="popLayout">
              {items.map((val: any, idx: number) => {
                const isElemHighlighted = highlights.includes(`${name}[${idx}]`) || isStructureHighlighted;
                return (
                  <motion.div
                    key={getStableKey(name, val, idx)}
                    layout
                    initial={{ scale: 0.5, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0, opacity: 0 }}
                    className={`w-16 h-16 rounded-full flex items-center justify-center font-mono font-bold text-2xl relative
                      ${isElemHighlighted
                        ? 'bg-cyan-500/30 text-cyan-200 border-2 border-cyan-400 shadow-[0_0_20px_rgba(34,211,238,0.5)]'
                        : 'bg-slate-800/80 text-slate-400 border border-slate-700'}`}
                  >
                    {renderValue(val)}
                    <span className="absolute -top-1 -right-1 w-5 h-5 bg-slate-950 border border-slate-800 rounded-full text-[8px] flex items-center justify-center text-slate-500">
                      {idx}
                    </span>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        </div>
      </div>
    );
  };

  const renderArray = (name: string, data: any, highlights: string[]) => {
    let items: any[] = [];
    if (typeof data === 'string') items = data.length > 100 ? data.slice(0, 100).split('') : data.split('');
    else if (Array.isArray(data)) items = data;
    else if (data?.values) items = data.values;
    else if (typeof data === 'object' && data !== null) items = Object.values(data);
    else items = [data];

    // Limit array size for rendering performance
    const maxItems = 50;
    const isTruncated = items.length > maxItems;
    const displayItems = isTruncated ? items.slice(0, maxItems) : items;

    const renderItem = (item: any): string => {
      if (item === null || item === undefined) return 'null';
      if (typeof item === 'string') {
        return item.length > 10 ? item.slice(0, 10) + '..' : item;
      }
      if (typeof item === 'number') {
        if (!isFinite(item)) return String(item);
        return String(item);
      }
      if (typeof item === 'boolean') return String(item);
      if (Array.isArray(item)) {
        if (item.length > 5) return `[${item.length}]`;
        return '[' + item.slice(0, 5).map(renderItem).join(',') + ']';
      }
      if (typeof item === 'object') {
        const str = JSON.stringify(item);
        return str.length > 15 ? str.slice(0, 15) + '..' : str;
      }
      return String(item);
    };

    const isStructureHighlighted = highlights.includes(name);

    return (
      <div className="flex flex-col items-center gap-6 w-full group">
        <div className="flex items-center gap-3 px-6 py-3 bg-slate-900/60 border border-slate-800/50 rounded-xl">
          <Cpu size={14} className={isStructureHighlighted ? 'text-cyan-400' : 'text-slate-600'} />
          <h3 className={`text-xs font-mono uppercase tracking-[0.4em] font-black ${
            isStructureHighlighted ? 'text-cyan-400' : 'text-slate-500'
          }`}>
            {name}
          </h3>
        </div>
        <div className={`flex flex-wrap justify-center gap-2 p-6 bg-slate-950/40 border rounded-2xl backdrop-blur-sm transition-all duration-500 ${
          isStructureHighlighted ? 'border-cyan-500/50 shadow-[0_0_30px_rgba(34,211,238,0.15)]' : 'border-slate-800/30'
        }`}>
          <AnimatePresence mode="popLayout">
            {displayItems.map((item: any, idx: number) => {
              const isElemHighlighted = highlights.includes(`${name}[${idx}]`) || isStructureHighlighted;
              return (
                <motion.div
                  key={getStableKey(name, item, idx)}
                  layout
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  className={`w-14 h-14 flex flex-col items-center justify-center font-mono border-2 transition-all duration-300 rounded-xl relative
                    ${isElemHighlighted
                      ? 'bg-cyan-500/30 border-cyan-400 text-white shadow-[0_0_25px_rgba(34,211,238,0.5)] z-10 scale-105'
                      : 'bg-slate-900/90 border-slate-800 text-slate-500'}`}
                >
                  <span className="text-xl font-bold">{renderItem(item)}</span>
                  <span className={`text-[8px] font-bold absolute -bottom-1 -right-1 w-5 h-5 flex items-center justify-center rounded-lg bg-slate-950 border border-slate-800 ${isElemHighlighted ? 'text-cyan-400' : 'text-slate-700'}`}>
                    {idx}
                  </span>
                </motion.div>
              );
            })}
            {isTruncated && (
              <motion.div
                key="truncated-indicator"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="w-14 h-14 flex flex-col items-center justify-center font-mono border-2 border-dashed border-slate-700 rounded-xl text-slate-600"
              >
                <span className="text-xs">+{items.length - maxItems}</span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    );
  };

  const renderMap = (name: string, data: any, highlights: string[]) => {
    const entries = (typeof data === 'object' && data !== null) ? Object.entries(data) : [];
    const isStructureHighlighted = highlights.includes(name);

    const renderMapValue = (val: any): string => {
      if (val === null || val === undefined) return 'null';
      if (typeof val === 'string' || typeof val === 'number' || typeof val === 'boolean') {
        return String(val);
      }
      if (Array.isArray(val)) {
        return '[' + val.map(renderMapValue).join(',') + ']';
      }
      if (typeof val === 'object') {
        return JSON.stringify(val);
      }
      return String(val);
    };

    return (
      <div className="flex flex-col items-center gap-6 min-w-[320px]">
        <div className="flex items-center gap-3 px-6 py-3 bg-slate-900/60 border border-slate-800/50 rounded-xl">
          <Hash size={14} className={isStructureHighlighted ? 'text-fuchsia-500' : 'text-slate-600'} />
          <h3 className={`text-xs font-mono uppercase tracking-[0.4em] font-black ${
            isStructureHighlighted ? 'text-fuchsia-500' : 'text-slate-500'
          }`}>
            {name}
          </h3>
        </div>
        <div className={`flex flex-col gap-4 p-6 rounded-3xl border transition-all duration-500 w-full ${
          isStructureHighlighted
            ? 'border-fuchsia-500/50 bg-fuchsia-500/5 shadow-[0_0_40px_rgba(217,70,239,0.15)]'
            : 'border-slate-800/50 bg-slate-900/40'
        }`}>
          <div className="grid gap-2">
            <AnimatePresence mode="popLayout">
              {entries.map(([key, val], idx) => (
                <motion.div
                  key={`map-${name}-${idx}-${key}`}
                  layout
                  className="flex items-center justify-between bg-slate-950/80 p-3 rounded-xl border border-slate-800 hover:border-fuchsia-500/40 transition-colors"
                >
                  <span className="text-fuchsia-400 font-mono text-xs font-bold">{safeStringify(key)}</span>
                  <div className="h-px flex-1 mx-4 bg-slate-800/50"></div>
                  <span className="text-cyan-400 font-mono text-xs font-bold">{renderMapValue(val)}</span>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      </div>
    );
  };

  const renderContent = () => {
    try {
      if (!state || !state.data || Object.keys(state.data).length === 0) {
        return (
          <div className="flex flex-col items-center gap-4 text-slate-700 font-mono italic text-sm">
            <div className="w-12 h-12 rounded-full border-2 border-slate-800 border-t-cyan-500 animate-spin" />
            [ SYNCHRONIZING TRACE STATE ]
          </div>
        );
      }

      const { data, highlights = [], visual_type } = state;

      // Safety check: limit number of data entries to render
      const entries = Object.entries(data);
      const maxEntries = 20;
      const limitedEntries = entries.length > maxEntries
        ? [...entries.slice(0, maxEntries), ['...more', `+${entries.length - maxEntries} hidden`]]
        : entries;

      return (
        <div className="flex flex-col items-center justify-center gap-12 w-full py-12 min-h-full overflow-auto">
          {limitedEntries.map(([key, val]) => {
            try {
              // Handle overflow indicator
              if (key === '...more') {
                return (
                  <div key="overflow" className="text-slate-500 font-mono text-xs px-4 py-2 bg-slate-900/50 rounded-lg border border-slate-800">
                    {val}
                  </div>
                );
              }

              // Check if data is too large to render
              if (isDataTooLarge(val)) {
                return (
                  <div key={`large-${key}`} className="flex flex-col items-center gap-2 p-6 bg-slate-900/60 border border-slate-700 rounded-xl max-w-md">
                    <span className="text-cyan-400 font-mono text-xs uppercase font-bold">{key}</span>
                    <span className="text-slate-400 font-mono text-xs text-center">
                      Data too large to visualize ({Array.isArray(val) ? `${val.length} items` : 'complex structure'})
                    </span>
                    <span className="text-slate-600 font-mono text-[10px] max-w-full truncate">
                      {safeStringify(val, 200)}
                    </span>
                  </div>
                );
              }

              if (visual_type === 'heap') return <div key={`heap-${key}`}>{renderHeap(key, val, highlights)}</div>;
              if (visual_type === 'map') return <div key={`map-${key}`}>{renderMap(key, val, highlights)}</div>;
              if (visual_type === 'matrix' || isMatrix(val)) return <div key={`matrix-${key}`}>{renderMatrix(key, val as any[][], highlights)}</div>;
              return <div key={`array-${key}`}>{renderArray(key, val, highlights)}</div>;
            } catch (err) {
              console.error(`Error rendering ${key}:`, err, val);
              return (
                <div key={`error-${key}`} className="flex flex-col items-center gap-2 p-4 bg-red-900/20 border border-red-500/30 rounded-xl">
                  <span className="text-red-400 font-mono text-xs uppercase">{key}</span>
                  <span className="text-slate-400 font-mono text-xs">{safeStringify(val, 100)}</span>
                </div>
              );
            }
          })}
        </div>
      );
    } catch (err) {
      console.error('Error in renderContent:', err);
      return (
        <div className="flex flex-col items-center gap-4 text-red-400 font-mono text-sm p-8">
          <span className="text-lg">⚠️ Visualization Error</span>
          <span className="text-slate-500 text-xs">Check console for details</span>
        </div>
      );
    }
  };

  const getQuickDescription = () => {
    if (!commentary) return null;
    const cleaned = commentary.replace(/#{1,6}\s*/g, '').trim();
    const firstSentence = cleaned.split(/[.!?]\s+/)[0];
    return firstSentence && firstSentence.length > 10 && firstSentence.length < 200
      ? firstSentence
      : null;
  };

  const quickDesc = getQuickDescription();

  return (
    <div className="flex-1 relative flex flex-col overflow-hidden h-full w-full">
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none"
           style={{ backgroundImage: 'radial-gradient(#22d3ee 1px, transparent 1px)', backgroundSize: '40px 40px' }}></div>

      {quickDesc && !isBlockedByQuiz && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative z-30 mx-8 mt-6 mb-4"
        >
          <div className="bg-gradient-to-r from-cyan-900/40 via-slate-900/60 to-cyan-900/40 border-2 border-cyan-500/30 rounded-xl p-4 backdrop-blur-sm shadow-xl">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-cyan-500/20 border border-cyan-400/50 flex items-center justify-center">
                <span className="text-cyan-300 font-black text-sm">{stepId !== undefined ? stepId + 1 : '?'}</span>
              </div>
              <div className="flex-1">
                <div className="text-xs font-mono uppercase tracking-wider text-cyan-400/80 mb-1">What's Happening</div>
                <div className="text-white font-medium leading-relaxed text-sm">
                  {quickDesc}
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      <AnimatePresence>
        {isBlockedByQuiz && (
          <motion.div
            initial={{ opacity: 0, backdropFilter: 'blur(0px)' }}
            animate={{ opacity: 1, backdropFilter: 'blur(8px)' }}
            exit={{ opacity: 0, backdropFilter: 'blur(0px)' }}
            className="absolute inset-0 z-40 flex items-center justify-center bg-slate-950/40 pointer-events-none"
          >
            <div className="bg-slate-900 border-2 border-fuchsia-500 px-8 py-5 rounded-2xl flex items-center gap-5 shadow-[0_0_60px_rgba(217,70,239,0.4)]">
              <div className="w-12 h-12 rounded-full bg-fuchsia-500 flex items-center justify-center animate-pulse">
                <HelpCircle className="text-slate-950" size={28} />
              </div>
              <div className="flex flex-col">
                <span className="text-fuchsia-100 font-mono text-sm font-black tracking-widest uppercase">
                  Verification Required
                </span>
                <span className="text-slate-500 text-[10px] font-mono uppercase tracking-tight">System paused until check is resolved</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        layout
        className="w-full h-full flex items-center justify-center z-10"
      >
        {renderContent()}
      </motion.div>
    </div>
  );
};

export default VisualizerCanvas;
