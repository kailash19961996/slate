// src/utils/logger.js
export function makeLogger(scope) {
    const prefix = `[${scope}]`;
    return {
      step: (...args) => console.info(prefix, "➡️", ...args),
      info: (...args) => console.info(prefix, "ℹ️", ...args),
      warn: (...args) => console.warn(prefix, "⚠️", ...args),
      error: (...args) => console.error(prefix, "❌", ...args),
      debug: (...args) => console.debug(prefix, "🐛", ...args),
    };
  }
  