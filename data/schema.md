# Dataset Schema

All items:
- id
- name
- type
- tags[]
- shortSummary
- howToUse[]
- synergies[]
- countersOrRisks[]
- unlockOrAvailability
- updatedAt (ISO)
- sources[] {label,url}

Type-specific optional fields:
- cards: rarity, cost
- relics: rarity
- characters: role
- keywords: category
- builds: character, actFocus
