# AgentPress Skills

Skill packages copied from [anthropics/skills](https://github.com/anthropics/skills).
Each skill provides deterministic Python scripts for document manipulation — no LLM code generation needed.

## Available Skills

| Skill | Format | Key Scripts |
|---|---|---|
| `pptx/` | PowerPoint | `scripts/add_slide.py`, `scripts/office/pack.py`, `scripts/office/unpack.py` |
| `docx/` | Word | `scripts/office/pack.py`, `scripts/office/unpack.py`, `scripts/accept_changes.py` |
| `xlsx/` | Excel | `scripts/office/pack.py`, `scripts/office/unpack.py`, `scripts/recalc.py` |
| `pdf/` | PDF | `scripts/fill_fillable_fields.py`, `scripts/extract_form_field_info.py` |
| `skill-creator/` | Meta | `scripts/package_skill.py`, `scripts/run_eval.py` |

## How AgentPress Uses These

The **Designer agent** (`app/agents/designer.py`) calls these scripts directly instead of
asking the LLM to generate document code from scratch.

### PPTX workflow
```python
from app.skills.pptx.scripts.office.unpack import unpack   # unzip to XML
from app.skills.pptx.scripts.office.pack import pack       # rezip to .pptx
from app.skills.pptx.scripts.add_slide import create_slide_from_layout
```

### DOCX workflow
```python
from app.skills.docx.scripts.office.unpack import unpack
from app.skills.docx.scripts.office.pack import pack
```

### XLSX workflow
```python
from app.skills.xlsx.scripts.office.unpack import unpack
from app.skills.xlsx.scripts.office.pack import pack
from app.skills.xlsx.scripts.recalc import recalc
```

## Creating a New Skill

Use the `skill-creator` skill as a guide. A skill needs:

```
my-skill/
├── SKILL.md          # Instructions + frontmatter (name, description, triggers)
├── scripts/          # Executable Python scripts
│   └── main.py
└── references/       # Supporting docs, templates, examples
```

The `SKILL.md` frontmatter tells the system when to load the skill:
```yaml
---
name: my-skill
description: Brief description used for skill discovery
triggers:
  - keyword1
  - keyword2
---
```

## Skill Registry

The Designer agent reads `app/tools/skills_registry.json` to know which skills are available.
Auto-generated skills from the Meta-Engineer are also registered there.
