# Six-Perspective Analysis

Launch six parallel Opus subagents to analyze the user's financial and life situation from different expert perspectives. This provides a comprehensive, multi-angle view that catches blind spots.

## Prerequisites
- Must have completed `/analyze` or have a thorough understanding of the user's financial data
- Must have had a conversation with the user about their life context (work, health, habits, goals)

## How to Use

Gather the full context first through conversation. You need to know:
- Income, expenses, savings, debt
- Work situation (hours, stress, career trajectory)
- Health habits (sleep, exercise, diet, caffeine)
- Living situation and any planned changes
- Family obligations
- Career goals and timeline

Then launch SIX parallel Agent calls, each with the full context and a specific analytical lens:

### Agent 1: Financial Planner
Focus: Pure numbers. Budget viability, emergency fund targets, tax optimization (TFSA vs RRSP vs FHSA), insurance gaps, debt assessment, monthly budget prescription.

### Agent 2: Life Coach
Focus: Work-life balance, burnout risk, reactive vs planned living, identity patterns (e.g., "built tough" as a trap), social connections, the question they're not asking themselves.

### Agent 3: Career Mentor
Focus: Market value assessment, resume positioning, job hop timing, salary negotiation strategy, skill development priorities, networking approach.

### Agent 4: Health & Wellness Specialist
Focus: Sleep quality, caffeine dependence, nutrition gaps, exercise as keystone habit, burnout stage assessment, specific protocols (not generic advice), when to see a doctor.

### Agent 5: Immigration / Expat Advisor
Focus: Remittance optimization, credit building strategy, NRI account management, tax implications, cultural adjustment, immigrant-specific financial milestones.

### Agent 6: Behavioral Economist
Focus: Cognitive biases in spending data, environmental design, habit formation research, nudge architecture, the tracking effect, one highest-evidence intervention.

## After All Six Return

Synthesize:
1. **Where all six agree** — these are non-negotiable actions
2. **Where they disagree** — present the tensions and let the user decide
3. **Priority stack** — ordered list of interventions
4. **The one question** each perspective wants the user to answer

Save the full output to `docs/YYYY-MM-DD-six-perspectives.md`.

## Important
- Each agent gets the FULL context (they start with zero knowledge)
- Use model: opus for all six agents
- Run all six in parallel (run_in_background: true)
- Wait for all six before synthesizing
- Be specific in each prompt — include actual numbers from the database, not summaries
