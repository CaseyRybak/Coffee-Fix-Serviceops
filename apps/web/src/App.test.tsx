import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { renderToStaticMarkup } from "react-dom/server";

import { App } from "./App";

describe("App", () => {
  it("renders the service operations shell without public automation claims", () => {
    const html = renderToStaticMarkup(<App />);

    assert.match(html, /Coffee Fix ServiceOps/);
    assert.match(html, /Intake queue/);
    assert.match(html, /Technician dispatch/);
    assert.doesNotMatch(html, /\bAI\b/i);
  });
});
