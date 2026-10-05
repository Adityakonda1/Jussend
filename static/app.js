async function api(url, options={}) {
  const res = await fetch(url, {
    headers: {"Content-Type":"application/json"},
    ...options
  });
  const data = await res.json();
  if (!res.ok || data.ok === false) throw new Error(data.error || "Request failed");
  return data;
}

function toast(message) {
  const el=document.getElementById("toast");
  el.textContent=message;
  el.classList.add("show");
  setTimeout(()=>el.classList.remove("show"),2600);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[c]));
}

function card(d) {
  const disabled = d.status === "approved" || d.status === "rejected";
  return `
  <article class="card" id="draft-${d.id}">
    <div class="card-head">
      <div class="meta">
        <div class="sender">${escapeHtml(d.sender)}</div>
        <div class="subject">${escapeHtml(d.subject)}</div>
        <div class="reason">${escapeHtml(d.reason)}</div>
      </div>
      <div class="score">${d.score}/100</div>
    </div>
    <div class="card-body">
      <div class="original">
        <div class="label">Incoming email</div>
        <div class="email-text">${escapeHtml(d.original)}</div>
      </div>
      <div class="draft">
        <div class="label">Jussend draft</div>
        <textarea id="body-${d.id}" ${disabled ? "disabled":""}>${escapeHtml(d.approved || d.generated)}</textarea>
      </div>
    </div>
    <div class="card-actions">
      ${!disabled ? `<button class="secondary" onclick="regenerate(${d.id})">Regenerate</button>
      <button class="danger" onclick="rejectDraft(${d.id})">Reject</button>
      <button class="primary" onclick="approve(${d.id})">Approve & save Gmail draft</button>` : `<span class="status">${escapeHtml(d.status)}</span>`}
    </div>
  </article>`;
}

async function load() {
  try {
    const drafts=await api("/api/drafts");
    const container=document.getElementById("drafts");
    if (!drafts.length) {
      container.innerHTML='<div class="empty">No reply drafts yet. Click <b>Scan inbox</b> to find conversations that need you.</div>';
    } else {
      container.innerHTML=drafts.map(card).join("");
    }
  } catch(e) { toast(e.message); }
}

async function connectGmail() {
  try {
    const result=await api("/api/connect",{method:"POST"});
    document.getElementById("connection").textContent="Connected: "+result.email;
    toast("Gmail connected");
  } catch(e) {
    toast(e.message);
  }
}

async function scan() {
  toast("Scanning inbox…");
  try {
    const result=await api("/api/scan",{method:"POST"});
    document.getElementById("scanInfo").textContent=`Last scan created ${result.created} new draft(s).`;
    await load();
    toast(`Created ${result.created} draft(s)`);
  } catch(e) { toast(e.message); }
}

async function approve(id) {
  const body=document.getElementById(`body-${id}`).value;
  try {
    await api(`/api/drafts/${id}/approve`,{
      method:"POST", body:JSON.stringify({body})
    });
    toast("Approved — saved as a Gmail draft");
    await load();
  } catch(e) { toast(e.message); }
}

async function rejectDraft(id) {
  try {
    await api(`/api/drafts/${id}/reject`,{method:"POST"});
    toast("Draft rejected");
    await load();
  } catch(e) { toast(e.message); }
}

async function regenerate(id) {
  try {
    const result=await api(`/api/drafts/${id}/regenerate`,{method:"POST"});
    document.getElementById(`body-${id}`).value=result.body;
    toast("Draft regenerated");
  } catch(e) { toast(e.message); }
}

async function toggleScheduler(enabled) {
  try {
    const result=await api("/api/scheduler",{
      method:"POST",body:JSON.stringify({enabled})
    });
    toast(result.enabled ? "Recurring scans enabled" : "Recurring scans disabled");
  } catch(e) { toast(e.message); }
}

load();
