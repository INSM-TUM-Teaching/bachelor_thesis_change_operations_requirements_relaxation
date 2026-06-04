# Relaxing Change Operation Requirements Through Human-In-The-Loop Variant Selection

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This project provides a console-based application for automated business process redesign (BPR). It extends the baseline approach by Andree et al. to handle cases where change operations are rejected as infeasible due to unsatisfied structural requirements — even when the operations themselves are semantically valid. Rather than rejecting such operations, the application detects the failure condition, applies an appropriate solution strategy, and guides the user through any remaining decisions via a human-in-the-loop interface.

The application is modeling-language independent, operating on an **activity relationships matrix** and **acceptance sequences** as its central process representation.

## Background

Change operations can only be implemented if a set of operation-specific structural requirements hold. For example, parallelizing activities `{A, C}` in a sequential process `A → B → C` fails because activity `B` lies between them, making the placement of the parallelized fragment ambiguous. A human modeler would resolve this by either moving `B` outside the set or expanding the set to `{A, B, C}`. This work automates exactly that resolution step.

Failure conditions are classified into three types:

| Failure Condition                    | Affected Operations   | Description                                                        |
| ------------------------------------ | --------------------- | ------------------------------------------------------------------ |
| **Activities happening in between**  | Parallelize, Collapse | Interfering activities block placement of the new fragment         |
| **Contradictions between inputs**    | Insert, Modify, Move  | Provided dependencies conflict with the existing process structure |
| **Violation of locked dependencies** | All operations        | The change operation alters a dependency designated as locked      |

For each failure condition, the application applies a dedicated solution strategy and, where multiple structural variants are possible, presents them to the user for selection.

## Solution Strategies

### Activities Happening In Between

Two strategies are offered:

- **Move activities**: All activities in the target set are moved to a single anchor position chosen by the user, eliminating any activities in between.
- **Expand the set**: The interfering activities are included in the parallelization/collapse set. This option is only offered when five or fewer activities are in between.

### Contradictions Between Inputs & Locked Dependency Violations

Both conditions are resolved using the **skeleton solution strategy**:

1. A set of _skeleton sequences_ is derived from the required dependencies (change operation inputs and locked dependencies). Each skeleton sequence is a valid structural template encoding the required ordering and co-occurrence of constrained activities.
2. Each acceptance sequence of the process is matched to the most similar skeleton sequence using a configurable **similarity score** (occurrence-based, ordering-based, or combined).
3. Acceptance sequences are adapted to conform to their matched skeleton sequence, preserving as much of the original process structure as possible while guaranteeing all required dependencies are satisfied.

For locked dependency violations, **dependency relaxation** is also offered: if the new dependency type after a change operation is a valid relaxation of the locked type (e.g., equivalence `⟺` relaxed to implication `⇒`), the user is asked whether to accept the relaxation before the skeleton strategy is applied.

## Key Features

- **Modeling language independent**: Operates on an abstract activity relationships matrix, not tied to any specific notation.
- **11 supported change operations**: Full coverage of basic and composite behavioral redesign operations.
- **Three failure condition handlers**: Automated detection and resolution of all identified structural failure conditions.
- **Human-in-the-loop variant selection**: Where multiple structural adaptations are valid, the user selects the preferred variant.
- **Locked dependencies**: Critical activity dependencies can be designated as locked and are preserved (or relaxed with user confirmation) across all change operations.
- **Configurable similarity scoring**: Users choose whether to prioritize preserving existential dependencies (occurrence similarity), temporal dependencies (ordering similarity), or a balanced combination.
- **YAML import/export**: Process models can be loaded from and exported to a human-readable `.yaml` format.

## Supported Change Operations

**Basic operations:**

- **Insert**: Add a new activity with specified temporal and/or existential dependencies.
- **Remove**: Remove an existing activity from the process.
- **Modify**: Change the temporal and/or existential dependencies between two activities.

**Composite operations:**

- **Move** (Insert + Remove): Move an activity to a new position.
- **Replace** (Remove + Insert): Replace an existing activity with a new one.
- **Parallelize** (Modify): Make a set of activities executable in any order.
- **Collapse** (Remove + Insert): Abstract a set of activities into a single sub-process activity.
- **De-collapse** (Remove + Insert): Expand a sub-process activity into its constituent activities.
- **Swap** (Insert + Remove): Swap the positions and dependencies of two activities.
- **Skip** (Modify): Make an activity optional.
- **Condition update** (Modify): Make an activity's execution conditional on another activity.

## How It Works

The application follows a three-step transformation cycle:

1. **Matrix → Acceptance sequences**: The activity relationships matrix is translated into the complete set of valid execution traces (acceptance sequences).
2. **Apply change operation**: The change operation is applied directly to the acceptance sequences. If a structural requirement is not met, the appropriate solution strategy is triggered.
3. **Acceptance sequences → Matrix**: The modified acceptance sequences are translated back into an activity relationships matrix, automatically capturing all primary and secondary dependency changes.

## Technology Stack

- **Language**: Python 3.10+
- **Interface**: Console application
- **Data format**: YAML (via PyYAML)

## Getting Started

### Prerequisites

- Python 3.10 or newer

### Installation & Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/thecodeflo/thesis_redesign_relaxation.git
   cd thesis_redesign_relaxation
   ```

2. **Create and activate a virtual environment:**

   ```bash
   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate

   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

## Using the Application

The application guides the user through the following steps:

**Step 1 — Load a process model**

Choose to provide the process as a `.yaml` file or by entering acceptance sequences manually. Acceptance sequences are derived from the input to build the activity relationships matrix.

**Step 2 — Lock dependencies (optional)**

Specify activity pairs whose temporal and/or existential dependencies must not be altered. The application will either refuse the change operation or apply a solution strategy to preserve the locks.

**Step 3 — Select and configure a change operation**

Choose one of the 11 supported change operations and provide the required input parameters (e.g., activity names, dependency types).

**Step 4 — Review and confirm**

If a failure condition is detected, the application presents available solution strategies or structural variants for user selection. For dependency relaxation, explicit confirmation is required before the lock is loosened.

**Step 5 — Export (optional)**

The resulting activity relationships matrix can be exported to a `.yaml` file. Further change operations can then be applied to the modified or original matrix.

## YAML File Format

```yaml
metadata:
  activities: [A, B, C]
dependencies:
  - from: A
    to: B
    temporal:
      type: direct
      direction: forward
    existential:
      type: equivalence
      direction: both
  - from: B
    to: C
    temporal:
      type: direct
      direction: forward
    existential:
      type: equivalence
      direction: both
```

Each entry in `dependencies` defines the pairwise relationship between two activities. Temporal types include `direct` and `eventual`; existential types include `equivalence`, `negated_equivalence`, `implication`, `or`, and `nand`.

## Evaluation

The solution strategies were validated against all failure cases identified during development (10 workflow control-flow patterns, 11 change operations) and evaluated for generalizability on five unseen process structures composed from combinations of workflow patterns. Key results:

- **Activities in between**: 11/11 cases resolved (100%).
- **Contradictions between inputs**: 61/64 cases resolved (three cases involve activity elimination treated as out of scope).
- **Locked dependency violations**: 11/11 cases resolved (100%).
- **Generalizability**: All applicable failure conditions resolved across all five unseen process structures.

## Project Context

This application was developed as part of a Bachelor's thesis at the Chair for Information Systems, Technical University of Munich.

- **Author**: Florian Alexander Stupp
- **Supervisor**: M.Sc. Kerstin Andree
- **Examiner**: Prof. Dr. Luise Pufahl
- **Submission**: June 2026

The baseline change operation algorithms this work extends are available at [INSM-TUM/business-process-redesign](https://github.com/INSM-TUM/business-process-redesign).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
