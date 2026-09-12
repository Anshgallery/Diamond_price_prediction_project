/**
 * GemForecast AI — Client Side Platform Utilities
 */

document.addEventListener("DOMContentLoaded", function () {
  // 1. Sample Certificate Autofill
  const sampleSelector = document.getElementById("sample-cert-select");
  if (sampleSelector) {
    sampleSelector.addEventListener("change", function () {
      const selected = this.value;
      if (!selected) return;

      const samples = {
        "2458921840": {
          report_number: "2458921840",
          origin_type: "Natural",
          carat: 1.01,
          cut: "Ideal",
          color: "E",
          clarity: "VVS1",
          depth: 61.7,
          table: 57.0,
          x: 6.45,
          y: 6.48,
          z: 3.99,
          polish: "Excellent",
          symmetry: "Excellent",
          fluorescence: "None",
          asking_price: 6800
        },
        "5221789034": {
          report_number: "5221789034",
          origin_type: "Natural",
          carat: 1.52,
          cut: "Very Good",
          color: "F",
          clarity: "VS2",
          depth: 61.6,
          table: 58.0,
          x: 7.35,
          y: 7.39,
          z: 4.54,
          polish: "Excellent",
          symmetry: "Very Good",
          fluorescence: "Faint Blue",
          asking_price: 12500
        },
        "6439012345": {
          report_number: "6439012345",
          origin_type: "Lab-Grown",
          carat: 2.01,
          cut: "Ideal",
          color: "D",
          clarity: "VS1",
          depth: 61.9,
          table: 56.0,
          x: 8.08,
          y: 8.12,
          z: 5.01,
          polish: "Excellent",
          symmetry: "Excellent",
          fluorescence: "None",
          asking_price: 1800
        }
      };

      const cert = samples[selected];
      if (cert) {
        for (const [key, val] of Object.entries(cert)) {
          const el = document.getElementById(key);
          if (el) {
            el.value = val;
            el.dispatchEvent(new Event("change"));
          }
        }
      }
    });
  }

  // 2. Real-time Live Proportion & Dimension Validator
  const tableInput = document.getElementById("table");
  const depthInput = document.getElementById("depth");
  const xInput = document.getElementById("x");
  const yInput = document.getElementById("y");
  const propBadge = document.getElementById("proportion-live-badge");

  function checkProportions() {
    if (!propBadge) return;
    const t = parseFloat(tableInput?.value) || 0;
    const d = parseFloat(depthInput?.value) || 0;
    const x = parseFloat(xInput?.value) || 0;
    const y = parseFloat(yInput?.value) || 0;

    if (t > 0 && d > 0) {
      if (t >= 54 && t <= 57 && d >= 61 && d <= 62.5) {
        propBadge.innerHTML = `<span class="gem-badge badge-success">Tolkowsky Ideal Proportions (T: ${t}%, D: ${d}%)</span>`;
      } else if (t >= 53 && t <= 59 && d >= 59.5 && d <= 63.5) {
        propBadge.innerHTML = `<span class="gem-badge badge-info">GIA Excellent Cut Range (T: ${t}%, D: ${d}%)</span>`;
      } else if (d > 64 || t > 62) {
        propBadge.innerHTML = `<span class="gem-badge badge-warning">Proportion Warning: Risk of Light Leakage</span>`;
      } else {
        propBadge.innerHTML = `<span class="gem-badge badge-secondary">Commercial Cut (T: ${t}%, D: ${d}%)</span>`;
      }
    }
  }

  [tableInput, depthInput, xInput, yInput].forEach((el) => {
    if (el) el.addEventListener("input", checkProportions);
  });

  // 3. Asking Price Live Margin Calculator on Results Page
  const liveAskingInput = document.getElementById("live-asking-price-input");
  const liveMarginDisplay = document.getElementById("live-margin-calc-display");
  const valuationMidpointVal = parseFloat(document.getElementById("valuation-midpoint-hidden")?.value) || 0;

  if (liveAskingInput && liveMarginDisplay && valuationMidpointVal > 0) {
    liveAskingInput.addEventListener("input", function () {
      const ask = parseFloat(this.value) || 0;
      if (ask <= 0) {
        liveMarginDisplay.innerHTML = `<span class="gem-badge badge-secondary">Enter asking price</span>`;
        return;
      }
      const delta = valuationMidpointVal - ask;
      const pct = ((delta / ask) * 100).toFixed(1);
      if (delta >= 0) {
        liveMarginDisplay.innerHTML = `<span class="gem-badge badge-success">+$${delta.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} (+${pct}%) Margin vs Fair Value</span>`;
      } else {
        liveMarginDisplay.innerHTML = `<span class="gem-badge badge-danger">-$${Math.abs(delta).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} (${pct}%) Premium above Fair Value</span>`;
      }
    });
  }
});

// 4. Dossier Print Utility
function printDossier() {
  window.print();
}
