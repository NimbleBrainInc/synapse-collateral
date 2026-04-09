"""UI resource loader for Collateral Studio.

In development: run `cd ui && npm run dev` for HMR via Vite.
In production: `cd ui && npm run build` produces a single-file HTML bundle
at ui/dist/index.html, which the server reads and serves as a ui:// resource.

Fallback: if no built UI exists, serves the original self-contained HTML
that works without Synapse.
"""

from pathlib import Path

_UI_DIR = Path(__file__).resolve().parent.parent.parent / "ui" / "dist"


def load_ui() -> str:
    """Load the built single-file HTML, or fall back to inline HTML."""
    built = _UI_DIR / "index.html"
    if built.exists():
        return built.read_text()
    return FALLBACK_HTML


# Minimal fallback — the original self-contained UI.
# Works without Synapse, without a build step.
FALLBACK_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Collateral Studio</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #ffffff; --fg: #1a1a1a; --muted: #6b7280;
    --border: #e5e7eb; --accent: #2563eb; --accent-hover: #1d4ed8;
    --card-bg: #f9fafb; --surface: #f3f4f6; --danger: #ef4444;
  }
  .dark {
    --bg: #111827; --fg: #f3f4f6; --muted: #9ca3af;
    --border: #374151; --accent: #3b82f6; --accent-hover: #60a5fa;
    --card-bg: #1f2937; --surface: #0f172a; --danger: #f87171;
  }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg); color: var(--fg);
    display: flex; flex-direction: column; height: 100vh; overflow: hidden;
  }
  nav {
    display: flex; align-items: center;
    border-bottom: 1px solid var(--border);
    padding: 0 1rem; height: 40px; flex-shrink: 0;
  }
  nav .logo { font-weight: 600; font-size: 0.85rem; margin-right: 1.5rem; }
  nav a {
    padding: 0.5rem 0.75rem; font-size: 0.8rem; color: var(--muted);
    text-decoration: none; border-bottom: 2px solid transparent; line-height: 26px;
  }
  nav a:hover { color: var(--fg); }
  nav a.active { color: var(--accent); border-bottom-color: var(--accent); }
  .view { display: none; flex: 1; overflow: hidden; }
  .view.active { display: flex; }
  #documents-view { flex-direction: column; padding: 1.5rem 2rem; overflow-y: auto; }
  .doc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
  .doc-header h1 { font-size: 1.1rem; }
  .doc-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 0.75rem; }
  .doc-card {
    padding: 1rem; border-radius: 8px; border: 1px solid var(--border);
    background: var(--card-bg); cursor: pointer; transition: border-color 0.15s;
  }
  .doc-card:hover { border-color: var(--accent); }
  .doc-card .name { font-weight: 600; font-size: 0.9rem; margin-bottom: 0.25rem; }
  .doc-card .meta { font-size: 0.72rem; color: var(--muted); }
  .doc-card-new {
    display: flex; align-items: center; justify-content: center;
    border: 2px dashed var(--border); color: var(--muted); font-size: 0.85rem; min-height: 80px;
  }
  .doc-card-new:hover { border-color: var(--accent); color: var(--accent); }
  .dialog-overlay {
    display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.4);
    z-index: 100; align-items: center; justify-content: center;
  }
  .dialog-overlay.open { display: flex; }
  .dialog {
    background: var(--bg); border: 1px solid var(--border); border-radius: 12px;
    padding: 1.5rem; width: 360px; max-width: 90vw; box-shadow: 0 8px 30px rgba(0,0,0,0.2);
  }
  .dialog h3 { font-size: 1rem; margin-bottom: 1rem; }
  .starter-opts { display: flex; flex-direction: column; gap: 0.35rem; margin-top: 0.5rem; }
  .starter-opt {
    display: flex; align-items: center; gap: 0.5rem; padding: 0.45rem 0.6rem;
    border: 1px solid var(--border); border-radius: 6px; cursor: pointer;
    font-size: 0.8rem; background: var(--card-bg);
  }
  .starter-opt:hover { border-color: var(--accent); }
  .starter-opt.sel { border-color: var(--accent); }
  .starter-opt input[type="radio"] { accent-color: var(--accent); }
  #editor-view {
    flex-direction: column; align-items: center; background: var(--surface);
  }
  .editor-bar {
    display: flex; align-items: center; gap: 0.5rem;
    padding: 0.5rem 1rem; width: 100%; border-bottom: 1px solid var(--border);
    background: var(--bg); flex-shrink: 0;
  }
  .editor-bar .doc-title {
    font-weight: 600; font-size: 0.85rem; margin-right: auto;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .editor-bar .doc-title .starter-badge {
    font-weight: 400; font-size: 0.7rem; color: var(--muted);
    background: var(--surface); padding: 0.15rem 0.4rem; border-radius: 3px; margin-left: 0.5rem;
  }
  .preview-area {
    flex: 1; display: flex; flex-direction: column; align-items: center;
    justify-content: center; padding: 1.5rem; overflow: auto; width: 100%;
  }
  .preview-area img {
    max-width: 100%; max-height: calc(100vh - 160px);
    box-shadow: 0 2px 20px rgba(0,0,0,0.12); border-radius: 3px;
  }
  .page-nav {
    display: flex; gap: 0.75rem; align-items: center; margin-top: 0.75rem;
    font-size: 0.8rem; color: var(--muted);
  }
  .page-nav button {
    background: var(--bg); border: 1px solid var(--border); border-radius: 4px;
    padding: 0.2rem 0.6rem; color: var(--fg); cursor: pointer; font-size: 0.75rem;
  }
  .page-nav button:disabled { opacity: 0.3; cursor: not-allowed; }
  .empty-state { color: var(--muted); font-size: 0.9rem; }
  #brand-view { flex-direction: column; padding: 1.5rem 2rem; overflow-y: auto; max-width: 560px; }
  .color-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 0.5rem; }
  .color-item { display: flex; align-items: center; gap: 0.5rem; }
  .color-swatch {
    width: 28px; height: 28px; border-radius: 4px; border: 1px solid var(--border);
    cursor: pointer; flex-shrink: 0; position: relative; overflow: hidden;
  }
  .color-swatch input[type="color"] {
    opacity: 0; position: absolute; inset: 0; width: 100%; height: 100%; cursor: pointer;
  }
  .color-label { font-size: 0.75rem; color: var(--muted); }
  h2 { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px;
       color: var(--muted); margin: 1rem 0 0.5rem; font-weight: 600; }
  h2:first-child { margin-top: 0; }
  select, input[type="text"] {
    width: 100%; padding: 0.45rem 0.6rem; border-radius: 6px;
    border: 1px solid var(--border); background: var(--card-bg);
    color: var(--fg); font-size: 0.8rem; font-family: inherit;
  }
  select:focus, input:focus { border-color: var(--accent); outline: none; }
  label { display: block; font-size: 0.75rem; color: var(--muted); margin: 0.4rem 0 0.2rem; }
  .btn {
    padding: 0.4rem 0.85rem; border-radius: 6px; border: none;
    font-size: 0.78rem; cursor: pointer; font-weight: 500; white-space: nowrap;
  }
  .btn-primary { background: var(--accent); color: #fff; }
  .btn-primary:hover { background: var(--accent-hover); }
  .btn-ghost { background: none; color: var(--muted); border: 1px solid var(--border); }
  .btn-ghost:hover { color: var(--fg); border-color: var(--fg); }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .spinner { display: none; color: var(--muted); font-size: 0.8rem; }
  .spinner.on { display: block; }
  .error { color: var(--danger); font-size: 0.78rem; }
  .actions { display: flex; gap: 0.5rem; justify-content: flex-end; }
</style>
</head>
<body>
<nav>
  <span class="logo">Collateral Studio</span>
  <a href="#/documents" data-view="documents">Documents</a>
  <a href="#/editor" data-view="editor">Editor</a>
  <a href="#/brand" data-view="brand">Brand</a>
</nav>
<div class="dialog-overlay" id="dlg-overlay">
  <div class="dialog">
    <h3>New Document</h3>
    <label>Name</label>
    <input type="text" id="dlg-name" placeholder="e.g. Acme Proposal Q2" />
    <h2>Start from</h2>
    <div class="starter-opts" id="dlg-starters">
      <label class="starter-opt sel"><input type="radio" name="starter" value="" checked /> Blank document</label>
    </div>
    <div class="actions" style="margin-top:1.25rem;">
      <button class="btn btn-ghost" id="dlg-cancel">Cancel</button>
      <button class="btn btn-primary" id="dlg-create">Create</button>
    </div>
  </div>
</div>
<div id="documents-view" class="view">
  <div class="doc-header"><h1>Documents</h1></div>
  <div class="doc-grid" id="doc-grid"></div>
</div>
<div id="editor-view" class="view">
  <div class="editor-bar">
    <span class="doc-title" id="doc-title">No document</span>
    <button class="btn btn-ghost" id="bar-save">Save</button>
    <button class="btn btn-ghost" id="bar-export">Export PDF</button>
  </div>
  <div class="preview-area">
    <div class="empty-state" id="editor-empty">Create or open a document to get started.</div>
    <img id="preview-img" style="display:none" />
    <div class="spinner" id="spinner">Rendering...</div>
    <div class="error" id="editor-error"></div>
    <div class="page-nav" id="page-nav" style="display:none">
      <button id="prev-btn">&laquo;</button>
      <span id="page-info">1 / 1</span>
      <button id="next-btn">&raquo;</button>
    </div>
  </div>
</div>
<div id="brand-view" class="view">
  <h1 style="font-size:1.1rem; margin-bottom:0.25rem;">Default Brand</h1>
  <p style="font-size:0.78rem; color:var(--muted); margin-bottom:1rem;">New documents inherit these settings. To customize a single document, use chat.</p>
  <h2>Preset</h2>
  <select id="brand-preset"></select>
  <h2>Colors</h2>
  <div class="color-grid" id="color-grid"></div>
  <h2>Fonts</h2>
  <div id="font-fields"></div>
  <details style="margin-top:0.75rem;">
    <summary style="font-size:0.75rem;color:var(--muted);cursor:pointer;">Available fonts</summary>
    <div id="font-list" style="max-height:200px;overflow-y:auto;font-size:0.72rem;color:var(--muted);margin-top:0.35rem;columns:2;column-gap:1rem;"></div>
  </details>
</div>
<script>
(function() {
  var P = {};
  function call(n, a) {
    return new Promise(function(ok, fail) {
      var id = crypto.randomUUID();
      P[id] = {ok:ok, fail:fail};
      window.parent.postMessage({jsonrpc:"2.0",method:"tools/call",id:id,params:{name:n,arguments:a||{}}}, "*");
      setTimeout(function() { if(P[id]){delete P[id]; fail(new Error("Timeout"));} }, 30000);
    });
  }
  function parse(r) {
    if(r&&r.content&&Array.isArray(r.content)){
      var t=r.content.map(function(c){return c.text||"";}).join("");
      try{return JSON.parse(t);}catch(e){return t;}
    } return r;
  }
  window.addEventListener("message", function(e) {
    var m=e.data; if(!m||m.jsonrpc!=="2.0") return;
    if(m.id&&P[m.id]){var p=P[m.id];delete P[m.id];m.error?p.fail(new Error(m.error.message)):p.ok(m.result);return;}
    if(m.method==="ui/initialize"&&m.params){if(m.params.theme&&m.params.theme.mode==="dark") document.body.classList.add("dark"); if(m.params.apiBase) apiBase=m.params.apiBase;}
    if(m.method==="ui/datachanged") refreshPreview();
  });
  var pages=[], pi=0, hasDoc=false, apiBase="";
  function nav(v) {
    document.querySelectorAll(".view").forEach(function(el){el.classList.remove("active");});
    document.querySelectorAll("nav a").forEach(function(a){a.classList.remove("active");});
    var el=document.getElementById(v+"-view"); if(el) el.classList.add("active");
    var lnk=document.querySelector('nav a[data-view="'+v+'"]'); if(lnk) lnk.classList.add("active");
    if(v==="documents") loadDocs();
    if(v==="editor" && hasDoc) refreshPreview();
    if(v==="brand") loadBrand();
  }
  document.querySelectorAll("nav a").forEach(function(a){a.addEventListener("click",function(e){e.preventDefault();location.hash=a.href.split("#")[1];});});
  window.addEventListener("hashchange",function(){nav((location.hash.replace("#/","")||"documents"));});
  async function loadDocs() {
    var r=await Promise.all([call("list_documents").then(parse), call("list_starters").then(parse)]);
    var docs=r[0], starters=r[1];
    var g=document.getElementById("doc-grid");
    var h='<div class="doc-card doc-card-new" id="new-btn">+ New Document</div>';
    for(var i=0;i<docs.length;i++){
      var d=docs[i]; var dt=d.modified?new Date(d.modified).toLocaleDateString():"";
      h+='<div class="doc-card" data-id="'+d.id+'"><div class="name">'+d.name+'</div><div class="meta">'+(d.starter_id||"custom")+" &middot; "+dt+"</div></div>";
    }
    g.innerHTML=h;
    document.getElementById("new-btn").addEventListener("click",function(){openDialog(starters);});
    g.querySelectorAll(".doc-card[data-id]").forEach(function(c){c.addEventListener("click",async function(){
      await call("open_document",{document_id:c.dataset.id});
      hasDoc=true; location.hash="#/editor"; loadEditorBar();
    });});
  }
  function openDialog(starters) {
    var ov=document.getElementById("dlg-overlay"), ni=document.getElementById("dlg-name"), so=document.getElementById("dlg-starters");
    var h='<label class="starter-opt sel"><input type="radio" name="starter" value="" checked /> Blank document</label>';
    for(var i=0;i<starters.length;i++) h+='<label class="starter-opt"><input type="radio" name="starter" value="'+starters[i].id+'" /> '+starters[i].name+"</label>";
    so.innerHTML=h;
    so.querySelectorAll(".starter-opt").forEach(function(o){o.addEventListener("click",function(){
      so.querySelectorAll(".starter-opt").forEach(function(x){x.classList.remove("sel");});
      o.classList.add("sel"); o.querySelector("input").checked=true;
    });});
    ni.value=""; ov.classList.add("open"); ni.focus();
  }
  document.getElementById("dlg-cancel").addEventListener("click",function(){document.getElementById("dlg-overlay").classList.remove("open");});
  document.getElementById("dlg-overlay").addEventListener("click",function(e){if(e.target===e.currentTarget)e.currentTarget.classList.remove("open");});
  document.getElementById("dlg-create").addEventListener("click",async function(){
    var name=document.getElementById("dlg-name").value.trim();
    if(!name){document.getElementById("dlg-name").focus();return;}
    var r=document.querySelector('input[name="starter"]:checked');
    var sid=r&&r.value?r.value:undefined;
    document.getElementById("dlg-overlay").classList.remove("open");
    await call("create_document",{name:name,starter_id:sid});
    hasDoc=true; location.hash="#/editor"; loadEditorBar();
  });
  document.getElementById("dlg-name").addEventListener("keydown",function(e){if(e.key==="Enter")document.getElementById("dlg-create").click();});
  async function loadEditorBar() {
    var ws=parse(await call("get_workspace"));
    var t=document.getElementById("doc-title");
    var badge=ws.starter_id?'<span class="starter-badge">'+ws.starter_id+'</span>':"";
    t.innerHTML=(ws.document_name||"Untitled")+badge;
    document.getElementById("editor-empty").style.display="none";
    await refreshPreview();
  }
  async function refreshPreview() {
    if(!hasDoc) return;
    document.getElementById("spinner").classList.add("on");
    try {
      var r=parse(await call("preview",{include_images:true}));
      pages=(r.pages||[]).map(function(p){return p.image_base64;});
      pi=0; showPage();
      document.getElementById("editor-error").textContent="";
    } catch(e){document.getElementById("editor-error").textContent=e.message;}
    document.getElementById("spinner").classList.remove("on");
  }
  function showPage(){
    var img=document.getElementById("preview-img"),pn=document.getElementById("page-nav");
    if(!pages.length){img.style.display="none";pn.style.display="none";return;}
    img.src="data:image/png;base64,"+pages[pi]; img.style.display="block";
    pn.style.display="flex";
    document.getElementById("page-info").textContent=(pi+1)+" / "+pages.length;
    document.getElementById("prev-btn").disabled=pi===0;
    document.getElementById("next-btn").disabled=pi===pages.length-1;
  }
  document.getElementById("prev-btn").addEventListener("click",function(){if(pi>0){pi--;showPage();}});
  document.getElementById("next-btn").addEventListener("click",function(){if(pi<pages.length-1){pi++;showPage();}});
  document.getElementById("bar-save").addEventListener("click",async function(){
    var b=document.getElementById("bar-save");
    try{await call("save_document");b.textContent="Saved!";b.disabled=true;setTimeout(function(){b.textContent="Save";b.disabled=false;},1500);}
    catch(e){document.getElementById("editor-error").textContent=e.message;}
  });
  document.getElementById("bar-export").addEventListener("click",async function(){
    try{
      var r=parse(await call("export_pdf",{include_data:true}));
      // Convert base64 PDF to binary array, then to a binary string the bridge can Blob-ify
      var bytes=Uint8Array.from(atob(r.pdf_base64),function(c){return c.charCodeAt(0);});
      var binStr=""; for(var i=0;i<bytes.length;i+=8192){binStr+=String.fromCharCode.apply(null,bytes.subarray(i,i+8192));}
      window.parent.postMessage({jsonrpc:"2.0",method:"synapse/download-file",params:{data:binStr,filename:r.filename||"document.pdf",mimeType:"application/pdf"}},"*");
    }catch(e){document.getElementById("editor-error").textContent=e.message;}
  });
  var TOKENS=["primary","accent","ink","dark","mid","subtle","faint","wash","paper","success","warning","error"];
  async function loadBrand(){
    var presets=parse(await call("list_brand_presets"));
    var sel=document.getElementById("brand-preset");
    sel.innerHTML=presets.map(function(p){return '<option value="'+p.id+'">'+p.name+'</option>';}).join("");
    sel.onchange=async function(){await call("configure_brand",{preset_id:sel.value,set_as_default:true});loadBrand();refreshPreview();};
    var brand; try{brand=parse(await call("configure_brand",{set_as_default:false}));}catch(e){brand={colors:{}};}
    var colors=brand.colors||{};
    var g=document.getElementById("color-grid");
    var h="";
    for(var i=0;i<TOKENS.length;i++){
      var t=TOKENS[i]; var v=colors[t]||"#000";
      h+='<div class="color-item"><div class="color-swatch" style="background:'+v+'"><input type="color" value="'+v+'" data-t="'+t+'" /></div><span class="color-label">'+t+'</span></div>';
    }
    g.innerHTML=h;
    g.querySelectorAll("input[type=color]").forEach(function(inp){inp.addEventListener("change",async function(){
      var o={};o[inp.dataset.t]=inp.value;
      await call("configure_brand",{colors:o,set_as_default:true});
      inp.parentElement.style.background=inp.value;
      refreshPreview();
    });});
    var fonts=brand.fonts||{};
    var FONT_KEYS=["display","body","code"];
    var ff=document.getElementById("font-fields"); var fh="";
    for(var fi=0;fi<FONT_KEYS.length;fi++){
      var fk=FONT_KEYS[fi]; var fv=fonts[fk]||"";
      fh+='<label>'+fk+'</label><input type="text" value="'+fv+'" data-fk="'+fk+'" />';
    }
    ff.innerHTML=fh;
    ff.querySelectorAll("input[type=text]").forEach(function(inp){inp.addEventListener("change",async function(){
      var o={};o[inp.dataset.fk]=inp.value;
      await call("configure_brand",{fonts:o,set_as_default:true});
      refreshPreview();
    });});
    try{
      var fl=parse(await call("list_fonts"));
      var ld=document.getElementById("font-list");
      ld.innerHTML=fl.map(function(f){return '<div>'+f+'</div>';}).join("");
    }catch(e){}
  }
  window.parent.postMessage({jsonrpc:"2.0",method:"ui/ready",params:{}},"*");
  if(!location.hash||location.hash==="#/") location.hash="#/documents";
  else nav(location.hash.replace("#/",""));
  window.dispatchEvent(new HashChangeEvent("hashchange"));
})();
</script>
</body>
</html>
"""
