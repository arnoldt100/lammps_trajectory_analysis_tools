# GitHub Copilot Engineering Standards

# AI Copilot Instructions: Interpretable Context Methodology

You must strictly adhere to the Interpretable Context Methodology when working
on this codebase. This ensures that context remains scoped, organized, and
easily understandable.

## 1. Feature Workspace Rule
* **Primary Directive:** Before modifying, creating, or analyzing any code for a specific feature, you must locate and review its corresponding **Feature Workspace Folder**.
* **Workspace Isolation:** Keep your operational context restricted to the relevant feature folder. Do not pull in unrelated files unless they are explicitly required for shared dependencies.
* **Context Verification:** Always check for an existing `README.md` or context file inside the specific feature workspace folder to understand the scope, constraints, and intent before writing code.
* **Updating Context:** If your changes alter the behavior, data flow, or state management of the feature, you must update the documentation or context files within that feature's workspace folder.

## 2. Rules for Creating New Feature Folders
When tasked with building a new feature from scratch, you must initialize its workspace using the following checklist:
* **Directory Generation:** Create a dedicated directory under the designated features root. Use `snake_case` or `kebab-case` naming conventions based on the surrounding modules.
* **Mandatory Context File:** Every new folder must start with a local `README.md` or `context.md` outlining the feature's goal, external dependencies, and structural boundaries.
* **Feature Logic Isolation:** Place all feature-specific logic, services, modules, or local configurations directly inside this folder. Avoid leaking feature-specific logic into the global scope.

## 3. Guidelines for Managing Shared Global Context
* **Minimize Global Noise:** Do not pollute global configuration files, application entry points, or core modules with logic unique to a single feature.
* **Shared Interfaces Only:** Only reference the global `src/` directory for truly universal utilities, core database engines, shared schemas, or global helper functions.
* **Centralized Testing Rule:** All tests must be placed in the root `./tests` folder. When writing tests for a specific feature, mirror the feature's structure inside the global `./tests` directory to keep things organized (e.g., using `pytest` conventions).
* **Cross-Dependencies:** If a feature workspace must interact with another feature workspace, you must explicitly document this dependency in the `README.md` of both respective feature folders.

## 4. Designated Directory Tree Structure
Always maintain and respect the project layout outlined below:

```text
```
.
├── .github/
│   └── copilot-instructions.md   # System rules
├── src/                          # Global engine, shared scientific constants, base classes
│   └── ...
├── tests/                        # Centralized mathematical and performance validation
│   ├── test_global/              # Global framework verification
│   └── features/                 # Feature-specific mathematical assertions
│       ├── test_signal_processing/ 
│       └── test_spectroscopy/
├── workspaces/
│   └── features/                 # Mathematical and analytical boundaries
│       ├── signal_processing/    # Feature Workspace Root
│       │   ├── algorithms.py     # High-performance processing logic (NumPy/SciPy)
│       │   ├── schemas.py        # Input/Output data shape specifications (Pydantic/Dataclasses)
│       │   └── README.md         # Mathematical models, equations, and context
│       └── spectroscopy/
│           ├── README.md
│           └── ...
└── pyproject.toml                # Build system (Poetry, Hatch, or Flit)
```

