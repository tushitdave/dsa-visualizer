# AlgoInsight - Implementation Session Log

**Date:** 2026-01-29
**Session Focus:** Bug Fixes, UI Improvements, Dynamic Complexity Analysis

---

## Summary of Changes Made

### 1. 2D Matrix Visualization (VisualizerCanvas.tsx)

**Problem:** Matrix inputs like `[[1,0,1],[1,1,1]]` were rendered as broken nested brackets: `[1,0,1[0,0,1[1,1]...`

**Solution:** Added dedicated matrix renderer with proper grid layout.

**Changes:**
- Added `isMatrix()` helper function (lines 17-22) to detect 2D arrays
- Added `renderMatrix()` function (lines 24-93) for proper grid display:
  - Shows row/column indices
  - Displays matrix dimensions (e.g., `[4×5]`)
  - Color codes: 1s = green, 0s = gray, highlighted = cyan
  - Supports cell-level highlighting (`matrix[row][col]`)
- Updated `renderContent()` to use matrix renderer when appropriate

**Files Modified:**
- `components/VisualizerCanvas.tsx`

---

### 2. UI Crash Prevention (VisualizerCanvas.tsx)

**Problem:** Complex data structures (like Word Break II output) caused React crash: "Objects are not valid as a React child"

**Solution:** Added comprehensive error handling and safe rendering.

**Changes:**
- Added `safeStringify()` helper function for safe value-to-string conversion
- Updated `getStableKey()` to handle objects/arrays safely
- Added try-catch wrapper around `renderContent()` with fallback error display
- Added individual try-catch for each data entry rendering
- Fixed `renderMap()` key to use index instead of raw value

**Files Modified:**
- `components/VisualizerCanvas.tsx`

---

### 3. Instrumenter Prompt Updates (instrumenter.py)

**Problem:** For mathematical problems like `sqrt(x=4)`, the LLM was creating fake arrays like `[1,2,3,4,5]` instead of using actual input.

**Solution:** Added specific guidance for single-value/mathematical problems.

**Changes:**
- Added "Mathematical/Single-Value Problems" section with sqrt example
- Added explicit warning: "Do NOT fabricate arrays like [1,2,3,4,5]"
- Updated "DATA TO INCLUDE" section with guidance for non-array inputs
- Added complete sqrt code example showing correct logging format
- Added warning messages: "⚠️ WRONG" and "✅ CORRECT" examples

**Files Modified:**
- `backend/app/agents/instrumenter.py`

---

### 4. Dynamic Complexity Analysis (AlgorithmComplexity.tsx)

**Problem:** Complexity section was hardcoded for Binary Search only:
- Always showed "Why O(log n)?"
- Always showed "Binary Search vs Linear Search"
- Hardcoded variables: `left`, `right`, `mid`
- Hardcoded key takeaway about binary search

**Solution:** Made entire component dynamic based on actual algorithm data.

**Changes:**
- Updated interface to accept rich complexity data:
  ```typescript
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
  ```
- "Why O(log n)?" → Now shows: "Why {complexity.time.average}?"
- "Binary Search vs Linear Search" → Now shows: "{fastLabel} vs {slowLabel}"
- Case descriptions now from data, not hardcoded
- Variables section now dynamic
- Math insight and key takeaway are optional and from data

**Files Modified:**
- `components/AlgorithmComplexity.tsx`

---

### 5. Narrator Rich Complexity Generation (narrator.py)

**Problem:** Narrator generated simple complexity: `{"time": "O(n)", "space": "O(1)"}`

**Solution:** Updated to generate rich complexity structure for dynamic frontend.

**Changes:**
- Updated example output format in prompt to show rich complexity structure
- Includes: best/average/worst cases, explanation, comparison_data
- Includes: space complexity with variables list
- Includes: case descriptions, math insight, key takeaway
- Updated fallback complexity structure for error cases
- Updated empty trace return to use rich structure

**Files Modified:**
- `backend/app/agents/narrator.py`

---

### 6. Narrator Component Update (Narrator.tsx)

**Problem:** Component expected simple `{time: string, space: string}` format only.

**Solution:** Made backwards compatible with both formats.

**Changes:**
- Added `SimpleComplexity` and `RichComplexity` interfaces
- Added `getComplexityDisplay()` function to handle both formats
- Extracts `average` or `worst` from rich format for display
- Falls back gracefully if data is missing

**Files Modified:**
- `components/Narrator.tsx`

---

## Files Modified Summary

| File | Changes |
|------|---------|
| `components/VisualizerCanvas.tsx` | Matrix renderer, error handling, safe stringify |
| `components/AlgorithmComplexity.tsx` | Dynamic complexity display |
| `components/Narrator.tsx` | Support rich complexity format |
| `backend/app/agents/instrumenter.py` | Mathematical problem handling |
| `backend/app/agents/narrator.py` | Rich complexity generation |

---

## Testing Checklist

### Backend Mode Testing

**Prerequisites:**
- [ ] Backend running: `cd backend && uvicorn app.main:app --reload`
- [ ] Frontend running: `npm run dev`
- [ ] Backend shows "BACKEND ACTIVE" in UI header

**Test Cases:**

#### Test 1: Square Root Problem (Mathematical/Single-Value)
```
Problem: Given x = 4, return sqrt(x) rounded down.
Input: x = 4
Output: 2
```
**Expected:**
- [ ] Visualization shows `x: 4`, NOT `INPUT_ARRAY: [1,2,3,4,5]`
- [ ] Shows `low`, `high`, `mid` boundaries
- [ ] Complexity shows actual algorithm complexity, not hardcoded Binary Search

#### Test 2: 2D Matrix Problem
```
Problem: Maximal Rectangle
Input: matrix = [["1","0","1","0","0"],["1","0","1","1","1"],["1","1","1","1","1"],["1","0","0","1","0"]]
Output: 6
```
**Expected:**
- [ ] Matrix displays as proper 2D grid
- [ ] Row and column indices visible
- [ ] 1s highlighted in green, 0s in gray
- [ ] No UI crash

#### Test 3: Word Break II (Complex Output)
```
Problem: Word Break II
Input: s = "catsanddog", wordDict = ["cat","cats","and","sand","dog"]
Output: ["cats and dog","cat sand dog"]
```
**Expected:**
- [ ] UI does NOT crash (was crashing before)
- [ ] If error, shows error message instead of blank screen
- [ ] Console shows helpful error details

#### Test 4: Two Sum (Array Problem)
```
Problem: Two Sum
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
```
**Expected:**
- [ ] Visualization uses actual array values
- [ ] Complexity shows "Hash Map vs Brute Force" or "Two Pointer vs Brute Force"
- [ ] NOT "Binary Search vs Linear Search"

#### Test 5: Valid Parentheses (Stack Problem)
```
Problem: Valid Parentheses
Input: s = "()[]{}"
Output: true
```
**Expected:**
- [ ] Visualization shows stack operations
- [ ] Complexity shows "Stack-Based vs Brute Force"
- [ ] Complexity explanation references stack operations

#### Test 6: Longest Palindromic Substring (String Problem)
```
Problem: Longest Palindrome
Input: s = "babad"
Output: "bab" or "aba"
```
**Expected:**
- [ ] Shows actual string "babad"
- [ ] Expand-around-center visualization
- [ ] Complexity shows O(n²) with explanation

---

### Cloud Mode Testing

**Prerequisites:**
- [ ] Backend NOT running (or stop it)
- [ ] Frontend shows "CLOUD MODE" in UI header
- [ ] Valid API key in `.env.local`

**Test Cases:**

#### Test 1: Basic Array Problem
```
Problem: Find maximum in array [3, 1, 4, 1, 5, 9, 2, 6]
```
**Expected:**
- [ ] Cloud mode generates visualization
- [ ] Shows actual array values
- [ ] Complexity analysis present

#### Test 2: String Problem
```
Problem: Reverse string "hello"
```
**Expected:**
- [ ] Shows actual string
- [ ] Step-by-step reversal
- [ ] Quizzes appear during visualization

---

## Known Issues / Limitations

1. **LLM Variability**: The instrumenter LLM may still sometimes create incorrect visualizations despite prompt improvements. This is inherent to LLM behavior.

2. **Complexity Data**: The narrator LLM needs to generate the rich complexity structure. If it fails, fallback shows "N/A" values.

3. **Comparison Data**: The `comparison_data` array in complexity needs to match the algorithm type for the chart to work correctly.

4. **Old Cached Data**: If testing after changes, clear browser cache or hard refresh to ensure new code is loaded.

---

## Next Steps

### Immediate (Testing Phase)
1. [ ] Run all test cases in Backend Mode
2. [ ] Run all test cases in Cloud Mode
3. [ ] Document any failures or unexpected behavior
4. [ ] Fix any critical issues found

### Short-term Improvements
1. [ ] Add more algorithm-specific comparison_data templates
2. [ ] Improve LLM prompt for consistent complexity generation
3. [ ] Add loading states for complexity chart
4. [ ] Cache algorithm complexity data to reduce LLM calls

### Long-term Enhancements
1. [ ] Pre-computed complexity data for common algorithms
2. [ ] User feedback on visualization quality
3. [ ] Algorithm detection to auto-select visualization type
4. [ ] Mobile-responsive matrix visualization

---

## How to Debug Issues

### UI Crash / Blank Screen
1. Open browser DevTools (F12)
2. Check Console tab for errors
3. Look for "Error rendering" messages
4. Check which data key caused the issue

### Wrong Visualization Data
1. Check backend logs for:
   - "Using example inputs:" - shows what inputs were extracted
   - "Selected Strategy:" - shows which algorithm was chosen
2. Check if `example_inputs` is being passed through pipeline

### Complexity Shows Wrong Values
1. Check if narrator is generating rich complexity structure
2. Look for `comparison_data` in response
3. Verify `getComparisonKeys()` is detecting algorithm type

### Backend Not Responding
1. Check if backend is running: `curl http://localhost:8000/`
2. Check backend logs for errors
3. Verify environment variables are set

---

## Environment Setup Reminder

### Backend (.env)
```bash
API_KEY=your_gemini_api_key
AZURE_OPENAI_API_KEY=your_azure_key 
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_API_VERSION=2024-08-01-preview
AZURE_DEPLOYMENT_NAME=gpt-4o
```

### Frontend (.env.local)
```bash
VITE_API_KEY=your_gemini_api_key
```

---

## Commands Reference

```bash
# Start backend
cd backend
uvicorn app.main:app --reload

# Start frontend
npm run dev

# Check backend health
curl http://localhost:8000/

# View backend logs
# Check terminal running uvicorn

# Clear frontend cache
# Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
```

---

---

## Session 2: 2026-02-03

**Session Focus:** Empty Frame Data Bug Fix

---

### 7. Empty Frame Data in Visualization (narrator.py)

**Problem:** Frames were being returned with empty `data: {}` objects, causing the frontend to show fallback "STEP/STATUS" data instead of actual algorithm visualization.

**Error Observed:**
```json
{
  "step_id": 0,
  "commentary": "Step 0: Processing...",
  "state": {
    "visual_type": "array",
    "data": {},
    "highlights": ["triangle"]
  },
  "quiz": null
}
```

**Root Causes Identified:**
1. LLM generating frames with empty `data` objects
2. `_post_process_narrative` not robustly handling all edge cases
3. No handling for `data_entries` format (alternative data structure)
4. Highlights referencing non-existent keys (e.g., "triangle" when data is empty)
5. `raw_trace` could be None causing potential errors
6. Frame-to-trace index mismatch when LLM consolidates steps

**Solution:** Enhanced `_post_process_narrative` function with robust fallback logic.

**Changes to `_post_process_narrative`:**

1. **Null Safety:**
   ```python
   if raw_trace is None:
       raw_trace = []
   ```

2. **Handle `data_entries` Format:**
   ```python
   if 'data_entries' in state and state['data_entries']:
       converted_data = {}
       for entry in data_entries:
           if isinstance(entry, dict) and 'name' in entry and 'values' in entry:
               converted_data[entry['name']] = entry['values']
       state['data'] = converted_data
   ```

3. **Improved Fallback Logic:**
   - Search multiple trace entries if first ones are empty
   - Use `min(frame_idx, len(raw_trace) - 1)` to avoid index errors
   - Create minimal fallback with `STEP` and `STATUS` as last resort
   - Include `input_data` in fallback if available

4. **Highlight Validation:**
   - Filter out highlights referencing non-existent keys
   - Add first data key as default highlight if none valid

5. **Type Validation:**
   - Ensure `data` is always a dict
   - Ensure `highlights` is always a list

6. **Extensive Logging:**
   - Log frame count and trace entry count
   - Log when empty data is detected
   - Log fallback actions taken
   - Final validation to catch any remaining issues

**Changes to `run_narrator_with_provider` and `run_narrator`:**

1. **Try-catch around post-processing:**
   ```python
   try:
       narrative = _post_process_narrative(narrative, trace_data)
   except Exception as post_err:
       logger.error(f"Post-processing failed: {post_err}")
       # Manual fallback for each frame
   ```

2. **Verification Logging:**
   ```python
   empty_count = sum(1 for f in narrative.get('frames', [])
                     if not f.get('state', {}).get('data'))
   if empty_count > 0:
       logger.warning(f"Warning: {empty_count} frames still have empty data")
   ```

**Files Modified:**
- `backend/app/agents/narrator.py`

---

## Updated Files Summary

| File | Session | Changes |
|------|---------|---------|
| `components/VisualizerCanvas.tsx` | 1 | Matrix renderer, error handling |
| `components/AlgorithmComplexity.tsx` | 1 | Dynamic complexity display |
| `components/Narrator.tsx` | 1 | Rich complexity format support |
| `backend/app/agents/instrumenter.py` | 1 | Mathematical problem handling |
| `backend/app/agents/narrator.py` | 1, 2 | Rich complexity + Empty frame fix |

---

## Next Steps (Session 2)

### Immediate Actions
1. [x] Implement robust `_post_process_narrative` function
2. [x] Add null safety for `raw_trace`
3. [x] Handle `data_entries` format conversion
4. [x] Add extensive debug logging
5. [ ] **Restart backend server** to pick up changes
6. [ ] Test with various algorithm problems
7. [ ] Monitor backend logs for new debug output

### Verification Steps
After restarting the backend, check logs for:
- `Post-processing X frames with Y raw trace entries`
- `Frame N: Empty data detected, attempting fallback`
- `Frame N: Used raw trace vars from step M`
- `Post-processing complete: All N frames have valid data`

### If Issues Persist
1. Check backend logs for specific frame numbers with issues
2. Verify `trace_data` from tracer has `vars` populated
3. Check if LLM is generating `data_entries` vs `data` format
4. Consider adding frontend fallback in `apiService.ts` as safety net

### Commands to Test
```bash
# Restart backend with reload
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Watch backend logs for debug output
# Look for "[narrator]" prefixed messages

# Test with a simple problem first
# Problem: Two Sum
# Input: nums = [2,7,11,15], target = 9
```

---

## Debug Log Messages Reference

### Success Path
```
[narrator] Post-processing 15 frames with 47 raw trace entries
[narrator] Extracted input_data from first trace: <class 'list'>, len=4
[narrator] Frame 0: Final data keys: ['INPUT_ARRAY', 'POINTERS'], highlights: ['INPUT_ARRAY']
...
[narrator] Post-processing complete: All 15 frames have valid data
[narrator] Generated 15 narrative frames
```

### Fallback Path
```
[narrator] Post-processing 15 frames with 47 raw trace entries
[narrator] No input_data could be extracted from raw trace
[narrator] Frame 0: Empty data detected, attempting fallback
[narrator] Frame 0: Used raw trace vars from step 0
[narrator] Frame 3: Created minimal fallback data
...
[narrator] Post-processing complete: All 15 frames have valid data
```

### Error Path
```
[narrator] Post-processing 15 frames with 0 raw trace entries
[narrator] No input_data could be extracted from raw trace
[narrator] Frame 0: Empty data detected, attempting fallback
[narrator] Frame 0: Created minimal fallback data
[narrator] Warning: 5 frames still have empty data after post-processing
```

---

## Session 3: 2026-02-04

**Session Focus:** Input Data Display, Quiz Validation, and Option Shuffling

---

### 8. Input Data Display in Visual Walkthrough (narrator.py)

**Problem:** Visual walkthrough showed empty boxes instead of actual input data (e.g., "catsanddog" for Word Break II).

**Root Cause:** The `_post_process_narrative` function wasn't receiving `normalized_data` which contains the original input variables extracted from the problem.

**Solution:** Updated both call sites to pass `normalized_data` to `_post_process_narrative`.

**Changes:**
- Updated function signature: `def _post_process_narrative(narrative: dict, raw_trace: list, normalized_data: dict = None)`
- Line 321: `narrative = _post_process_narrative(narrative, trace_data, normalized_data)`
- Line 1131: `narrative = _post_process_narrative(narrative, trace_data, normalized_data)`
- Added extensive logging to track input extraction from `normalized_data.example_inputs[0].input_vars`

**Files Modified:**
- `backend/app/agents/narrator.py`

---

### 9. Quiz Answer Validation (narrator.py)

**Problem:** Quiz answers were sometimes incorrect (e.g., showing "4" as correct when frame data showed "5").

**Solution:** Added `_validate_quiz_answer` function that validates quiz answers against visible frame data.

**Changes:**
- New function `_validate_quiz_answer(quiz, frame_data, commentary)`:
  - Extracts key-value pairs from frame data
  - Matches question keywords to data keys (e.g., "total candies" -> TOTAL_CANDIES)
  - Validates and corrects the answer if it doesn't match expected value
- Applied validation to both fresh results and cached results in `pipeline.py`

**Files Modified:**
- `backend/app/agents/narrator.py`
- `backend/app/pipeline.py`

---

### 10. Quiz Option Shuffling with End-Option Handling (narrator.py)

**Problem:**
1. Quiz answers always appeared as Option 1 (no randomization)
2. "None of the above" and similar options were appearing at random positions

**Solution:** Added `_shuffle_quiz_options` function with special handling for "end options".

**Changes:**
- New function `_shuffle_quiz_options(quiz)`:
  - Identifies "end options" (None of the above, All of the above, Cannot be determined, etc.)
  - Separates regular options from end options
  - Only shuffles regular options
  - Appends end options at the end (position 4)
  - Tracks and updates the correct answer index after shuffling

**End Option Patterns Handled:**
```python
end_option_patterns = [
    "none of the above", "all of the above", "cannot be determined",
    "skip this step", "this step is not needed", "restart the algorithm",
    "return an error", "continue without changes", "alternative approach"
]
```

**Files Modified:**
- `backend/app/agents/narrator.py`

---

### 11. Realistic Fallback Quiz Options (narrator.py)

**Problem:** When quizzes had fewer than 4 options, they were padded with "Option 4" placeholder.

**Solution:** Replaced placeholder with realistic fallback options.

**Changes:**
```python
fallback_options = [
    "None of the above",
    "Skip this step",
    "This step is not needed",
    "Cannot be determined",
    "All of the above",
    "Restart the algorithm",
    "Return an error",
    "Continue without changes"
]
```

**Files Modified:**
- `backend/app/agents/narrator.py`

---

### 12. Quiz Validation for Cached Results (pipeline.py)

**Problem:** Cached results bypassed quiz validation, causing stale/incorrect quiz answers.

**Solution:** Added quiz validation to the INSTANT cache path.

**Changes:**
```python
from app.agents.narrator import _validate_quiz_answer, _shuffle_quiz_options

# In INSTANT PATH section:
for frame in result.get('frames', []):
    quiz = frame.get('quiz')
    if quiz:
        frame_data = frame.get('state', {}).get('data', {})
        commentary = frame.get('commentary', '')
        _validate_quiz_answer(quiz, frame_data, commentary)
```

**Files Modified:**
- `backend/app/pipeline.py`

---

## Updated Files Summary (Session 3)

| File | Changes |
|------|---------|
| `backend/app/agents/narrator.py` | Input data extraction, quiz validation, option shuffling |
| `backend/app/pipeline.py` | Quiz validation for cached results |

---

## Testing Checklist (Session 3)

### Input Data Display Test

**Problem: Word Break II**
```
Input: s = "catsanddog", wordDict = ["cat","cats","and","sand","dog"]
```

**Expected:**
- [ ] Visual walkthrough shows "catsanddog" as input string
- [ ] Characters displayed in boxes, not empty
- [ ] Backend logs show: "Extracted input 's' from normalized_data"
- [ ] Backend logs show: "Frame 0: Added input keys from normalized_data: ['S']"

### Quiz Validation Test

**Any problem with numeric values in frame data**

**Expected:**
- [ ] Quiz answer matches the visible data in the frame
- [ ] If data shows `TOTAL_CANDIES: 5`, quiz answer about "total candies" should be "5"
- [ ] Backend logs show: "Validating quiz answer against frame data"

### Quiz Option Shuffling Test

**Expected:**
- [ ] Correct answer is NOT always Option 1
- [ ] "None of the above" always appears at Option 4 (last position)
- [ ] Other end options (Cannot be determined, etc.) also at end

---

## Commands to Test

```bash
# Restart backend to clear in-memory cache and load new code
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Watch for version marker in logs:
# "NARRATOR MODULE LOADED - VERSION 2026-02-04-v6 (Input Data Fix)"
# "POST-PROCESS v2026-02-04-v6 (Input Data Fix) STARTING"

# Watch for input extraction logs:
# "EXTRACTING INPUT DATA FROM normalized_data"
# "input_vars: {'s': 'catsanddog', 'wordDict': [...]}"
# "Added to input_data_dict: S = catsanddog"
```

---

**Last Updated:** 2026-02-04
**Status:** Input data fix implemented, quiz validation added, option shuffling complete. Restart backend to test.

To be done 4th-feb-2026

  Implementation Complete                                                                                                                                                                       
  I've implemented all three phases of the multi-user session support for Vercel deployment:                                                                                                 
  
  Phase 1: Environment-Based Configuration

  - services/apiService.ts: Changed hardcoded localhost:8000 to use import.meta.env.VITE_API_BASE_URL with fallback
  - .env.production: Created with VITE_API_BASE_URL placeholder for production deployment
  - .env.local: Updated with VITE_API_BASE_URL=http://localhost:8000
  - backend/app/main.py: Updated CORS to use ALLOWED_ORIGINS environment variable

  Phase 2: Session Tracking

  - services/apiService.ts: Added getSessionId() function using crypto.randomUUID() stored in sessionStorage
  - All fetch calls: Now include X-Session-ID header for request correlation
  - backend/app/utils/request_context.py: Added session_id field to RequestContext dataclass
  - backend/app/main.py: All endpoints (/analyze, /learn, /algorithm/generate) extract session ID from headers and include it in logging

  Phase 3: Secure Credential Management

  - backend/app/utils/credential_store.py: New module with SQLite + Fernet encryption for secure credential storage
  - backend/app/main.py: Added 5 new endpoints:
    - POST /session/store-credentials - Store encrypted credentials
    - GET /session/{session_id}/credentials - Get credential metadata
    - DELETE /session/{session_id} - Delete session credentials
    - GET /session/stats - Admin statistics
    - POST /session/cleanup - Clean expired sessions
  - /analyze and /learn endpoints: Updated to support stored credentials (priority: request body > stored > environment)
  - components/Sidebar.tsx: Updated to store credentials on backend and check for existing session credentials on load
  - backend/requirements.txt: Added cryptography>=41.0.0
  - backend/.env: Added template for ALLOWED_ORIGINS and CREDENTIAL_ENCRYPTION_KEY

  Files Modified/Created
  ┌───────────────────────────────────────┬──────────┐
  │                 File                  │  Action  │
  ├───────────────────────────────────────┼──────────┤
  │ services/apiService.ts                │ Modified │
  ├───────────────────────────────────────┼──────────┤
  │ .env.production                       │ Created  │
  ├───────────────────────────────────────┼──────────┤
  │ .env.local                            │ Modified │
  ├───────────────────────────────────────┼──────────┤
  │ backend/app/main.py                   │ Modified │
  ├───────────────────────────────────────┼──────────┤
  │ backend/app/utils/request_context.py  │ Modified │
  ├───────────────────────────────────────┼──────────┤
  │ backend/app/utils/credential_store.py │ Created  │
  ├───────────────────────────────────────┼──────────┤
  │ backend/requirements.txt              │ Modified │
  ├───────────────────────────────────────┼──────────┤
  │ backend/.env                          │ Modified │
  ├───────────────────────────────────────┼──────────┤
  │ components/Sidebar.tsx                │ Modified │
  └───────────────────────────────────────┴──────────┘
  Deployment Steps

  1. Deploy backend to Railway/Render/Fly.io
  2. Set environment variables on backend host:
    - ALLOWED_ORIGINS=https://your-app.vercel.app
    - CREDENTIAL_ENCRYPTION_KEY (generate with python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
  3. Set VITE_API_BASE_URL in Vercel to your backend URL
  4. Deploy frontend to Vercel
