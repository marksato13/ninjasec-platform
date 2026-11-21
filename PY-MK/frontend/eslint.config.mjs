// Flat config de ESLint 9. Sustituye a .eslintrc.json, que Next 16 ya no
// soporta: `next lint` fue eliminado y eslint-config-next@16 exige ESLint >=9
// con este formato. Equivale exactamente al anterior, que extendia
// next/core-web-vitals + next/typescript.
import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  globalIgnores([".next/**", "out/**", "build/**", "next-env.d.ts"]),
  {
    // Reglas NUEVAS de eslint-config-next@16 que marcan codigo preexistente.
    // Quedan en "warn", no en "error", para no bloquear el lint mientras se
    // salda la deuda -- pero NO se desactivan: hay que verlas.
    //
    // react-hooks/set-state-in-effect (13 casos) caza exactamente el
    // anti-patron que CLAUDE.md ya prohibia: "No useEffect para sincronizar
    // estado con datos de useQuery -- usar data ?? []". La regla llego antes
    // que el refactor. Pendiente 02-P-06.
    rules: {
      "react-hooks/set-state-in-effect": "warn",
      "react-hooks/purity": "warn",
      "@typescript-eslint/no-require-imports": "warn",
    },
  },
]);

export default eslintConfig;
