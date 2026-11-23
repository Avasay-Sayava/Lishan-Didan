const _ = undefined;

const TENSES = {
  PAST: "past",
  PERFECT: "perf",
  PRESENT: "pres",
  IRREALIS: "irr",
  IMPERATIVE: "imp",
  GERUND: "ger",
};

const VOWELS = ["a", "e", "i", "o", "u", "ə"];

const UNVOICED = ["∅", "h", "k", "x", "s", "š", "ṣ", "p", "f", "č", "t", "q"];

const VOICED = [
  "b",
  "v",
  "g",
  "j",
  "d",
  "w",
  "z",
  "ž",
  "y",
  "l",
  "m",
  "n",
  "γ",
  "r",
];

const CONSONANTS = [...UNVOICED, ...VOICED];
const STRESS_MARK = "\u0301";

const MORPHS = [
  "1s",
  "m_1s",
  "f_1s",
  "1p",
  "2s",
  "m_2s",
  "f_2s",
  "2p",
  "m_3s",
  "f_3s",
  "3p",
];

function stress(word, index) {
  if (typeof word !== "string") {
    throw new TypeError(
      `applyStress: Expected a string, received ${typeof word}: ${String(word)}`,
    );
  }

  if (typeof index !== "number" || Number.isNaN(index)) {
    throw new TypeError(
      `applyStress: Expected a numeric index, received ${typeof index}: ${String(index)}`,
    );
  }

  if (word.includes(STRESS_MARK)) {
    throw new Error(`applyStress: ${word} is already stressed`);
  }

  const segmenter = new Intl.Segmenter("en", { granularity: "grapheme" });
  const letters = Array.from(segmenter.segment(word)).map((s) => s.segment);

  const vowel_count = letters.reduce(
    (acc, letter) => acc + (VOWELS.includes(letter) ? 1 : 0),
    0,
  );
  if (index >= vowel_count || index < -vowel_count) {
    return word;
  }

  let target = ((index % vowel_count) + vowel_count) % vowel_count;

  if (letters.length === 0) {
    throw new Error(`applyStress: Could not segment word for stress: ${word}`);
  }

  let stressed = false;

  for (let i = 0; i < letters.length; i++) {
    if (VOWELS.includes(letters[i]) && target-- == 0) {
      letters[i] += "\u0301";
      stressed = true;
      break;
    }
  }

  if (!stressed) {
    throw new Error(
      `applyStress: Could not place stress on ${word} at index ${index}`,
    );
  }

  return letters.join("");
}

const s = stress;

const replaceIndex = (word, search, replace, index) => {
  const re = new RegExp(
    search.source ?? search.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"),
    (search.flags || "").replace("g", "") + "g",
  );

  const m = [...word.matchAll(re)];
  const t = m[index < 0 ? m.length + index : index];

  return t
    ? word.slice(0, t.index) + replace + word.slice(t.index + t[0].length)
    : word;
};

function run(fn, ...args) {
  return typeof fn === "function" ? fn(...args) : undefined;
}

const TEMPLATES = {
  3: (templates, [I, II, III]) => {
    templates[TENSES.IRREALIS] = () => `${I}a${II}ə${III}`;
    templates[TENSES.PERFECT] = () => `${I}${II}i${III}`;
    templates[TENSES.PRESENT] = () => `${I}a${II}o${III}`;
    templates[TENSES.IMPERATIVE] = () => `${I}${II}u${III}`;

    templates[TENSES.PAST] = () =>
      replaceIndex(templates[TENSES.PERFECT](), "i", "ə", -1);
    templates[TENSES.GERUND] = () => templates[TENSES.PRESENT]() + "é";

    templates[TENSES.PAST + "_base"] = ({ lamadPersonal }) =>
      s(templates[TENSES.PAST](), -1) + lamadPersonal;

    templates[TENSES.PERFECT + "_base"] = ({ copula }) =>
      templates[TENSES.PERFECT]() + s(copula, 0);

    templates[TENSES.PRESENT + "_base"] = ({ lamadCopula }) =>
      s(templates[TENSES.PRESENT](), -1) + lamadCopula;

    templates[TENSES.IRREALIS + "_base"] = ({ copula }) =>
      replaceIndex(templates[TENSES.IRREALIS](), "ə", "", -1) +
      s(copula, 0);
    templates[TENSES.IRREALIS + "_m_3s"] = () =>
      s(templates[TENSES.IRREALIS](), -1);

    templates[TENSES.IMPERATIVE + "_2s"] = () => templates[TENSES.IMPERATIVE]();
    templates[TENSES.IMPERATIVE + "_2p"] = () =>
      s(templates[TENSES.IMPERATIVE](), -1) + "un";
  },
  "3_I-∅": (templates, [_I, II, III]) => {
    templates[TENSES.PRESENT] = () => `i${II}a${III}`;

    templates[TENSES.GERUND] = () => templates[TENSES.PRESENT]() + "á";
  },
  "3_II-y/∅": (templates, [I, _II, III]) => {
    templates[TENSES.IRREALIS] = () => `${I}e${III}`;
    templates[TENSES.PRESENT] = () => `${I}iya${III}`;

    templates[TENSES.GERUND] = () => templates[TENSES.PRESENT]() + "á";
  },
  "3_III-y/∅": (templates, [I, II, _III]) => {
    templates[TENSES.IRREALIS] = () => `${I}a${II}e`;
    templates[TENSES.PERFECT] = () => `${I}${II}e`;
    templates[TENSES.IMPERATIVE] = () => `${I}${II}i`;

    templates[TENSES.IRREALIS + "_base"] = ({ copula }) =>
      `${I}a${II}` + s(copula, 0);
    templates[TENSES.IRREALIS + "_f_base"] = ({ copula }) =>
      `${I}a${II}y` + s(copula, 0);
    templates[TENSES.IRREALIS + "_3p"] = () => `${I}a${II}éni`;

    templates[TENSES.IMPERATIVE + "_2p"] = () =>
      s(templates[TENSES.IMPERATIVE](), -1) + "mun";
  },
  "3_II-w/∅": (templates, [I, _II, III]) => {
    templates[TENSES.IRREALIS] = () => `${I}o${III}`;
  },
};

const CLASSES = {
  3: (templates, [I, II, III]) => {
    TEMPLATES["3"](templates, [I, II, III]);
  },
  "3_I-∅": (templates, [_I, II, III]) => {
    CLASSES["3"](templates, ["", II, III]);

    TEMPLATES["3_I-∅"](templates, [_, II, III]);
  },
  "3_I-h/∅": (templates, [_I, II, III]) => {
    CLASSES["3"](templates, ["", II, III]);

    TEMPLATES["3_I-∅"](templates, [_, II, III]);
  },
  "3_II-y/∅": (templates, [I, _II, III]) => {
    CLASSES["3"](templates, [I, "", III]);

    TEMPLATES["3_II-y/∅"](templates, [I, _, III]);
  },
  "3_III-y/∅": (templates, [I, II, _III]) => {
    CLASSES["3"](templates, [I, II, "y"]);

    TEMPLATES["3_III-y/∅"](templates, [I, II, _]);
  },
  "3_II-w/∅": (templates, [I, _II, III]) => {
    CLASSES["3"](templates, [I, "w", III]);

    TEMPLATES["3_II-w/∅"](templates, [I, _, III]);
  },
  "3_I-∅_II-w/∅": (templates, [_I, _II, III]) => {
    CLASSES["3"](templates, ["", "w", III]);

    TEMPLATES["3_I-∅"](templates, [_, "w", III]);
    TEMPLATES["3_II-w/∅"](templates, ["", _, III]);
  },
};

function splitRoot(root) {
  if (typeof root !== "string") {
    throw new TypeError(
      `Root must be a hyphen-separated string in the form C1-C2-C3, received ${typeof root}`,
    );
  }

  const parts = root.split("-");

  if (parts.length !== 3 || parts.some((rad) => rad.trim() === "")) {
    throw new RangeError(
      `Root must be exactly 3 radicals separated by hyphens: C1-C2-C3, received ${JSON.stringify(root)}`,
    );
  }

  return parts.map((rad) => rad.trim());
}

function getRootClass(rawRoot) {
  const root = splitRoot(rawRoot);

  if (root.length !== 3) {
    throw new RangeError(
      `Root length must be exactly 3 radicals, received ${root.length}`,
    );
  }

  if (root.some((rad) => typeof rad !== "string" || rad.length === 0)) {
    throw new TypeError(
      `Each root radical must be a non-empty string, received ${JSON.stringify(root)}`,
    );
  }

  const features = [`${root.length}`];
  const [I, II, III] = root;

  if (I === "∅") {
    features.push("I-∅");
  }

  if (II === "y/∅") {
    features.push("II-y/∅");
  } else if (II === "w/∅") {
    features.push("II-w/∅");
  } else if (II.length === 2) {
    features.push("II-double");
  }

  if (III === "y/∅") {
    features.push("III-y/∅");
  }

  return features.join("_");
}

function generate(rawRoot, tense, morph) {
  const root = splitRoot(rawRoot);
  const tenseLevelForm = morph == null;

  if (!Object.values(TENSES).includes(tense)) {
    throw new Error(`Unknown tense: ${String(tense)}`);
  }

  if (!MORPHS.includes(morph) && !tenseLevelForm) {
    throw new Error(`Unknown morph: ${String(morph)}`);
  }

  if (root.length !== 3) {
    throw new RangeError(
      `Root length must be exactly 3 radicals, received ${root.length}`,
    );
  }

  if (root.some((rad) => typeof rad !== "string" || rad.length === 0)) {
    throw new TypeError(
      `Each root radical must be a non-empty string, received ${JSON.stringify(root)}`,
    );
  }

  const templates = {};
  let hasVelarization = false;
  const cleanRoot = root.map((rad) => {
    if (rad.includes("+")) {
      hasVelarization = true;
      return rad.replace(/\+/g, "");
    }
    return rad;
  });

  const personal = {
    "1s": "i",
    "1p": "an",
    m_2s: "ox",
    f_2s: "ax",
    "2p": "xun",
    m_3s: "ew",
    f_3s: "aw",
    "3p": "u",
  };

  const lamadPersonal = {
    "1s": "li",
    "1p": "lan",
    m_2s: "lox",
    f_2s: "lax",
    "2p": "lxun",
    m_3s: "le",
    f_3s: "la",
    "3p": "lu",
  };

  const copula = {
    m_1s: "en",
    f_1s: "an",
    "1p": "ex",
    m_2s: "et",
    f_2s: "at",
    "2p": "etun",
    m_3s: "",
    f_3s: "a",
    "3p": "i",
  };

  const lamadCopula = {
    m_1s: "len",
    f_1s: "lan",
    "1p": "lex",
    m_2s: "let",
    f_2s: "lat",
    "2p": "letun",
    m_3s: "le",
    f_3s: "la",
    "3p": "lu",
  };

  function build(args, form, morphKey, tArgs) {
    const key = `${form}_${morphKey}`;
    const template =
      templates[key] ||
      (morphKey.includes("f") && templates[`${form}_f_base`]) ||
      templates[`${form}_base`];
    args[key] = args[key] || run(template, tArgs);
  }

  function conjugate(args) {
    MORPHS.forEach((f) => {
      const jsonArgs = {
        copula: copula[f] || "",
        lamadCopula: lamadCopula[f] || "",
        personal: personal[f] || "",
        lamadPersonal: lamadPersonal[f] || "",
      };
      Object.values(TENSES).forEach((t) => {
        build(args, t, f, jsonArgs);
      });
    });
  }

  const cls = getRootClass(rawRoot);

  if (!CLASSES[cls]) {
    throw new Error(`Root class not found: ${cls}`);
  }

  const args = {};
  CLASSES[cls](templates, cleanRoot);
  conjugate(args);

  if (tenseLevelForm) {
    const directTemplate = templates[tense];
    if (typeof directTemplate === "function") {
      return directTemplate();
    }

    const key = `${tense}_default`;
    if (!(key in args)) {
      throw new Error(`Form not found for tense "${tense}" with no morph`);
    }

    return args[key];
  }

  const key = `${tense}_${morph}`;
  if (!(key in args)) {
    throw new Error(`Form not found for tense "${tense}" and morph "${morph}"`);
  }

  let result = args[key];

  if (typeof result !== "string") {
    throw new TypeError(
      `Generated form for ${key} must be a string, received ${typeof result}`,
    );
  }

  if (hasVelarization) {
    result = "+" + result;
  }

  return result;
}

export { TENSES, MORPHS, generate };

export default {
  TENSES,
  MORPHS,
  generate,
};
