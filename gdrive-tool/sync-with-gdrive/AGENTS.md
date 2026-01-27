# Codex Agent Instructions (Python / PySide6)

You are an AI coding agent working in this repository. Follow these rules strictly.

## 1) Project Structure Rules (MANDATORY)
- All Python code must be placed into files that follow the existing project structure:
  - Reusable UI widgets/components MUST live in: `src/components/`
  - Business logic / main execution logic MUST live in: `src/workers/`
  - Theme values (colors, spacing, etc.) MUST reference: `src/configs/configs.py` whenever applicable
  - App icons MUST be SVG assets referenced from: `src/assets/images/svg/`

Do NOT create new folders unless explicitly requested. Prefer extending existing files over creating new files.

---

## 2) Icon Rules (MANDATORY)
- NEVER use raw unicode icons (e.g. "⚙️", "🗑️", "✅", etc.).
- ALWAYS use SVG icons from `src/assets/images/svg/`.
- To render icons, ALWAYS use the helper function:
  - `get_svg_as_icon` from `src/utils/helpers`

If an icon is needed and no suitable SVG exists, report that the asset is missing and suggest a filename/path under `src/assets/images/svg/` (do not invent the SVG content unless explicitly asked).

---

## 3) Widget & Component Usage Rules (MANDATORY)
- For common widgets like `QLabel`, `QPushButton`, always prefer using the project’s wrapped versions from:
  - `src/components/`

Only use the original Qt widgets directly when there is a strong reason (e.g., a component does not exist in `src/components`, or special behavior requires the raw widget). In that case, briefly explain the reason.

For the following UI components, ALWAYS prefer project components from `src/components/`:
- Loading components  
- Tooltip components  
- Select box components  
- Divider components  
- Scrollable text components  

### Announcement / Dialog Rule (MANDATORY)
- Any announcement or message shown as a dialog MUST use:
  - `CustomAnnounce` class from `src/components/announcement.py`
- DO NOT use `QMessageBox` or custom ad-hoc dialog widgets for announcements unless explicitly requested.

### Base Widget Preference Rule (MANDATORY)
- Prefer using `QFrame` instead of `QWidget` as the base class for custom UI containers and components.
- Use `QWidget` only when `QFrame` is not appropriate or when explicitly required by the existing codebase.

---

## 4) Class Field Naming Rules (MANDATORY)
- Any internal field used inside a class MUST start with an underscore `_`.
  - Example: `_btn_save`, `_label_title`, `_worker`, `_state`, `_is_running`

Public fields should be avoided unless explicitly required by the existing codebase.

---

## 5) Styling Rules (VERY IMPORTANT)
When styling child widgets:
- You MUST style children ONLY via:
  1) setting `setObjectName("...")` on child widgets
  2) applying styles by calling `setStyleSheet(...)` on the PARENT container (or root widget)

DO NOT call `setStyleSheet(...)` directly on child widgets (unless explicitly requested).
DO NOT use inline per-child styling except objectName + parent stylesheet.

### Required Styling Pattern
- Create child widget → set `objectName`
- Parent widget → call `setStyleSheet` using `#ObjectName` selectors

---

## 6) Output & Change Discipline
- Make minimal changes required to satisfy the request.
- Do not refactor unrelated code.
- Keep naming and patterns consistent with the existing codebase.
- If unsure where something belongs (component vs worker), decide based on:
  - Reusable UI → `src/components/`
  - Business logic / execution flow → `src/workers/`

---

## 7) Before Implementing
When generating code:
- First, identify where the code should live (component vs worker).
- Reuse existing components and helpers whenever possible.
- Do not duplicate functionality that already exists in `src/components/` or `src/utils/`.

Follow these rules even if the user prompt does not explicitly repeat them.
