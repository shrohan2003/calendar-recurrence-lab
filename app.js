const slots = document.querySelector("#slots");
const results = document.querySelector("#results");
const download = document.querySelector("#download");
let mask = 22; // 10:00, 11:00 and 13:00 UTC.
let fileURL;

async function start() {
  const response = await fetch("cases.json");
  if (!response.ok) throw new Error("Results unavailable");
  const cases = await response.json();
  for (let index = 0; index < 6; index++) {
    const button = document.createElement("button");
    button.className = "slot";
    const hour = String(9 + index).padStart(2, "0") + ":00";
    button.setAttribute("aria-label", "Cancel " + hour + " UTC");
    button.innerHTML = '<span class="hour">' + hour + '</span><span class="state"></span>';
    button.onclick = () => { mask ^= 1 << index; render(); };
    slots.append(button);
  }
  function render() {
    const record = cases[mask];
    for (const [index, button] of [...slots.children].entries()) {
      const cancelled = Boolean(mask & (1 << index));
      button.setAttribute("aria-pressed", String(cancelled));
      button.lastChild.textContent = cancelled ? "Cancelled" : "Scheduled";
    }
    const rows = [["Expected", record.expected], ["Before the fix", record.before],
                  ["Proposed fix", record.proposed]];
    results.replaceChildren(...rows.map(([title, values]) => {
      const row = document.createElement("div");
      row.className = "row" + (values.join() !== record.expected.join() ? " mismatch" : "");
      const label = document.createElement("strong");
      label.textContent = title;
      const data = document.createElement("span");
      data.className = "rowdata";
      data.textContent = values.join(" · ") || "No meetings";
      row.append(label, data);
      return row;
    }));
    document.querySelector("#ics").textContent = record.ics;
    if (fileURL) URL.revokeObjectURL(fileURL);
    fileURL = URL.createObjectURL(new Blob([record.ics], {type: "text/calendar"}));
    download.href = fileURL;
  }
  render();
}
start().catch(() => {results.textContent = "Could not load recorded runs. Reload the page to retry.";});
