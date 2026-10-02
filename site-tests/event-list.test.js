import { test } from "node:test";
import assert from "node:assert/strict";
import { renderEventListInto } from "../site/js/event-list.js";

// Minimal stand-in for the .event-list element: just enough surface for
// renderEventListInto, counting how many click handlers get bound.
function fakeListEl() {
  return {
    innerHTML: "",
    dataset: {},
    clickHandlers: 0,
    addEventListener(type) {
      if (type === "click") this.clickHandlers += 1;
    },
  };
}

test("renderEventListInto: re-rendering into the same element binds the click handler only once", () => {
  // incidents-view.js re-renders into the same .event-list on every filter
  // change; stacked handlers cancel each other's toggle and cards stop expanding.
  const listEl = fakeListEl();
  renderEventListInto(listEl, []);
  renderEventListInto(listEl, []);
  renderEventListInto(listEl, []);
  assert.equal(listEl.clickHandlers, 1);
});
