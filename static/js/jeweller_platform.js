/**
 * India-First Jeweller AI Diamond Valuation Platform JavaScript
 */

document.addEventListener("DOMContentLoaded", function () {
    // 1. IGI PDF Drag & Drop Handling
    const dropzone = document.getElementById("igiDropzone");
    const fileInput = document.getElementById("igiFileInput");
    const uploadForm = document.getElementById("igiUploadForm");

    if (dropzone && fileInput) {
        dropzone.addEventListener("click", () => fileInput.click());

        ["dragenter", "dragover"].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add("dragover");
            });
        });

        ["dragleave", "drop"].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove("dragover");
            });
        });

        dropzone.addEventListener("drop", (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0 && files[0].type === "application/pdf") {
                fileInput.files = files;
                if (uploadForm) {
                    showLoadingIndicator("Extracting & Verifying IGI Certificate PDF...");
                    uploadForm.submit();
                }
            } else {
                alert("Please drop a valid IGI Certificate PDF file.");
            }
        });

        fileInput.addEventListener("change", () => {
            if (fileInput.files.length > 0) {
                if (uploadForm) {
                    showLoadingIndicator("Extracting & Verifying IGI Certificate PDF...");
                    uploadForm.submit();
                }
            }
        });
    }

    // 2. Interactive Buy/Sell Calculator on Appraisal Page
    const buyInput = document.getElementById("calcBuyPrice");
    const markupSlider = document.getElementById("calcMarkupSlider");
    const markupValue = document.getElementById("calcMarkupValue");
    const makingChargeInput = document.getElementById("calcMakingCharge");
    
    const outSellPrice = document.getElementById("outSellPrice");
    const outProfit = document.getElementById("outProfit");
    const outMargin = document.getElementById("outMargin");
    const outGst = document.getElementById("outGst");
    const outFinalCustomerPrice = document.getElementById("outFinalCustomerPrice");

    function updateLiveDealCalculator() {
        if (!buyInput || !markupSlider) return;

        const buyPrice = parseFloat(buyInput.value) || 0;
        const markupPct = parseFloat(markupSlider.value) || 25;
        const makingCharge = parseFloat(makingChargeInput ? makingChargeInput.value : 0) || 0;

        if (markupValue) markupValue.innerText = markupPct + "%";

        const sellPrice = Math.round(buyPrice * (1 + markupPct / 100) + makingCharge);
        const profit = Math.round(sellPrice - buyPrice);
        const marginPct = sellPrice > 0 ? ((profit / sellPrice) * 100).toFixed(1) : 0;
        const gst = Math.round(sellPrice * 0.03);
        const finalCustomer = sellPrice + gst;

        if (outSellPrice) outSellPrice.innerText = formatINR(sellPrice);
        if (outProfit) outProfit.innerText = formatINR(profit);
        if (outMargin) outMargin.innerText = marginPct + "%";
        if (outGst) outGst.innerText = formatINR(gst);
        if (outFinalCustomerPrice) outFinalCustomerPrice.innerText = formatINR(finalCustomer);
    }

    if (buyInput) buyInput.addEventListener("input", updateLiveDealCalculator);
    if (markupSlider) markupSlider.addEventListener("input", updateLiveDealCalculator);
    if (makingChargeInput) makingChargeInput.addEventListener("input", updateLiveDealCalculator);

    // 3. Indian Rupee Formatter Utility
    function formatINR(val) {
        if (!val || isNaN(val)) return "₹ 0";
        const amt = Math.round(val).toString();
        if (amt.length <= 3) return "₹ " + amt;

        const last3 = amt.substring(amt.length - 3);
        let other = amt.substring(0, amt.length - 3);
        const groups = [];
        while (other.length > 2) {
            groups.unshift(other.substring(other.length - 2));
            other = other.substring(0, other.length - 2);
        }
        if (other) groups.unshift(other);
        return "₹ " + groups.join(",") + "," + last3;
    }

    // 4. Loading Overlay Indicator
    function showLoadingIndicator(msg) {
        const overlay = document.createElement("div");
        overlay.id = "loadingOverlay";
        overlay.style.cssText = "position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(9,13,22,0.88);backdrop-filter:blur(8px);z-index:9999;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff;font-family:var(--font-sans);";
        overlay.innerHTML = `
            <div style="font-size:3rem;animation:spin 1.5s linear infinite;margin-bottom:1rem;">💎</div>
            <h3 style="font-family:var(--font-display);font-size:1.4rem;color:#F59E0B;margin-bottom:0.5rem;">IGI Gemological Intelligence</h3>
            <p style="color:#94A3B8;font-size:0.95rem;">${msg}</p>
            <style>@keyframes spin { 0% { transform: scale(1) rotate(0deg); } 50% { transform: scale(1.15) rotate(180deg); } 100% { transform: scale(1) rotate(360deg); } }</style>
        `;
        document.body.appendChild(overlay);
    }

    // 5. Global helper for sample buttons
    window.setSampleIgi = function(repNo) {
        const repInput = document.getElementById("igiReportInput");
        if (repInput) {
            repInput.value = repNo;
            const btn = document.getElementById("igiSearchBtn");
            if (btn) btn.click();
        }
    };
});
