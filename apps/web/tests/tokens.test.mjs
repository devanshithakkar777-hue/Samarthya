import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";

test("every declared text/background pair meets its WCAG contrast target", () => {
  const out = execFileSync("node", ["scripts/build-tokens.mjs"], { encoding: "utf8" });
  assert.doesNotMatch(out, /FAIL/);
  assert.match(out, /all declared pairs meet/);
});
