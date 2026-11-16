import { TENSES, MORPHS, generate } from "./lishan-conjugation.js";

const root = "h-w-y/∅";

const selectedMorphsByTense = {
  [TENSES.PAST]: ["1s", "1p", "m_2s", "f_2s", "2p", "m_3s", "f_3s", "3p"],
  [TENSES.PERFECT]: ["m_1s", "f_1s", "1p", "m_2s", "f_2s", "2p", "m_3s", "f_3s", "3p"],
  [TENSES.PRESENT]: ["m_1s", "f_1s", "1p", "m_2s", "f_2s", "2p", "m_3s", "f_3s", "3p"],
  [TENSES.IRREALIS]: ["m_1s", "f_1s", "1p", "m_2s", "f_2s", "2p", "m_3s", "f_3s", "3p"],
  [TENSES.IMPERATIVE]: ["2s", "2p"],
  [TENSES.GERUND]: [null],
};

const byTense = {};

for (const tense of Object.values(TENSES)) {
  const morphs = selectedMorphsByTense[tense] ?? [];
  byTense[tense] = [];

  for (const morph of morphs) {
    if (morph === null) {
      byTense[tense].push(generate(root, tense, null));
      continue;
    }

    if (!MORPHS.includes(morph)) {
      continue;
    }

    try {
      byTense[tense].push(generate(root, tense, morph));
    } catch {
      // Skip any morph that is intentionally not implemented for this tense.
    }
  }
}

console.log(JSON.stringify(byTense, null, 2));