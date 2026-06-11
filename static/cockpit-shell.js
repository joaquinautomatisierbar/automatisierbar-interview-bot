/* ============================================================
   automatisierbar · Cold-Call Cockpit 2.0 — shared shell
   Sidebar, auth gate, helpers, and dependency-free SVG charts.
   Loaded before each page's inline script. Pages call:
     Shell.ready(fn)   // fn runs once authed
   ============================================================ */
(function(){
  "use strict";

  const ICONS = {
    overview:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/></svg>',
    live:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.9.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></svg>',
    verlauf:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>',
    analyse:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>',
    logout:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>',
    bolt:'<svg viewBox="0 0 24 24" fill="currentColor"><path d="M13 2 4.5 13.5H11l-1 8.5L19.5 10H13l0-8z"/></svg>',
  };

  const NAV = [
    {page:"overview", href:"/voice/overview", label:"Übersicht",     icon:ICONS.overview},
    {page:"analyse",  href:"/voice/analyse",  label:"Analyse",       icon:ICONS.analyse},
    {page:"live",     href:"/voice/cockpit",  label:"Live-Cockpit",  icon:ICONS.live, live:true},
    {page:"verlauf",  href:"/voice/sessions", label:"Verlauf",       icon:ICONS.verlauf},
  ];

  const qs = new URLSearchParams(location.search);
  const esc = s => String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#39;");

  const Shell = {
    apiKey: qs.get("key") || "",
    _readyFn:null, _authed:false,

    hdr(extra){ const h = this.apiKey ? {"X-API-Key":this.apiKey} : {}; return Object.assign(h, extra||{}); },
    esc,
    pct(v){ return `${Math.round((v||0)*100)}%`; },
    chf(v){ return (v||0).toFixed(2); },
    dateShort(d){ return String(d||"").slice(5,10); },

    toast(m, ok){ const t=document.getElementById("toast"); if(!t)return; t.textContent=m; t.className="show"+(ok?" ok":""); clearTimeout(this._tt); this._tt=setTimeout(()=>t.className="",2800); },

    // sidebar budget gauge (spent/cap in CHF) — call from any page
    budget(spent, cap){
      const el=document.getElementById("bmFill"), v=document.getElementById("bmVal"), g=document.getElementById("bmGauge");
      if(!el)return;
      cap=cap||1; const ratio=Math.max(0,Math.min(1,spent/cap));
      el.style.width=(ratio*100)+"%";
      g.className="gauge"+(ratio>=0.9?" danger":ratio>=0.7?" warn":"");
      v.textContent=`${Math.round(spent)} / ${Math.round(cap)} CHF`;
    },
    setLive(on){ const it=document.querySelector('.nav-item[data-page="live"]'); if(it)it.classList.toggle("running",!!on); },

    ready(fn){ this._readyFn=fn; if(this._authed)fn(); },

    /* ---------- dependency-free SVG charts ---------- */

    // tiny inline sparkline → svg string
    sparkline(values, opts){
      opts=opts||{}; const w=opts.w||96, h=opts.h||26, col=opts.color||"var(--green)", pad=2;
      const v=(values||[]).filter(x=>x!=null);
      if(v.length<2) return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" width="${w}" height="${h}"></svg>`;
      const mn=Math.min(...v), mx=Math.max(...v), sp=(mx-mn)||1;
      const X=i=>pad+(w-2*pad)*i/(v.length-1), Y=val=>pad+(h-2*pad)*(1-(val-mn)/sp);
      const pts=v.map((val,i)=>`${X(i).toFixed(1)},${Y(val).toFixed(1)}`).join(" ");
      const area=`${pad},${h-pad} ${pts} ${(w-pad)},${h-pad}`;
      const gid="sg"+Math.round(X(v.length-1)+Y(v[v.length-1])*7+v.length*13);
      return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" width="100%" height="${h}">
        <defs><linearGradient id="${gid}" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="${col}" stop-opacity=".28"/><stop offset="1" stop-color="${col}" stop-opacity="0"/></linearGradient></defs>
        <polygon points="${area}" fill="url(#${gid})"/>
        <polyline points="${pts}" fill="none" stroke="${col}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/>
        <circle cx="${X(v.length-1).toFixed(1)}" cy="${Y(v[v.length-1]).toFixed(1)}" r="2.2" fill="${col}"/></svg>`;
    },

    // multi-series line/area chart → svg string (rows in chronological order)
    // cfg: { rows, series:[{get,color,label,area}], yMax?, yFmt?, marker?(row,i)->label }
    lineChart(cfg){
      const rows=cfg.rows||[], n=rows.length;
      const W=cfg.w||880, H=cfg.h||260, P={l:40,r:16,t:18,b:34}, iw=W-P.l-P.r, ih=H-P.t-P.b;
      if(!n) return `<svg viewBox="0 0 ${W} ${H}" width="100%"></svg>`;
      let yMax=cfg.yMax;
      if(yMax==null){ yMax=0; rows.forEach(r=>cfg.series.forEach(s=>{const v=s.get(r)||0; if(v>yMax)yMax=v;})); yMax=yMax*1.15||1; }
      const yFmt=cfg.yFmt||(v=>Math.round(v));
      const X=i=>P.l+(n===1?iw/2:iw*i/(n-1)), Y=v=>P.t+ih*(1-Math.max(0,Math.min(1,(v||0)/yMax)));
      let grid="";
      [0,.25,.5,.75,1].forEach(t=>{ const yy=P.t+ih*(1-t), val=yMax*t;
        grid+=`<line x1="${P.l}" y1="${yy}" x2="${W-P.r}" y2="${yy}" stroke="var(--border-2)" stroke-width="1" stroke-dasharray="2 4"/>`;
        grid+=`<text x="${P.l-7}" y="${yy+3}" text-anchor="end" font-size="10" fill="var(--text-dim)">${esc(yFmt(val))}</text>`; });
      let markers="";
      if(cfg.marker){ for(let i=0;i<n;i++){ const lab=cfg.marker(rows[i],i); if(lab){ const xx=X(i);
        markers+=`<line x1="${xx}" y1="${P.t}" x2="${xx}" y2="${H-P.b}" stroke="var(--text-dim)" stroke-dasharray="3 3" stroke-width="1"/>`;
        markers+=`<text x="${xx}" y="${P.t-5}" text-anchor="middle" font-size="9" fill="var(--text-muted)">${esc(lab)}</text>`; } } }
      let xl=""; const every=Math.max(1,Math.ceil(n/8));
      rows.forEach((r,i)=>{ if(i%every===0||i===n-1){ xl+=`<text x="${X(i)}" y="${H-P.b+16}" text-anchor="middle" font-size="9" fill="var(--text-dim)">${esc(cfg.x?cfg.x(r):"")}</text>`; } });
      let body="", defs="";
      cfg.series.forEach((s,si)=>{
        const pts=rows.map((r,i)=>`${X(i).toFixed(1)},${Y(s.get(r)).toFixed(1)}`).join(" ");
        if(s.area){ const gid="ar"+si;
          defs+=`<linearGradient id="${gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${s.color}" stop-opacity=".22"/><stop offset="1" stop-color="${s.color}" stop-opacity="0"/></linearGradient>`;
          body+=`<polygon points="${P.l},${P.t+ih} ${pts} ${W-P.r},${P.t+ih}" fill="url(#${gid})"/>`; }
        body+=`<polyline points="${pts}" fill="none" stroke="${s.color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>`;
        body+=rows.map((r,i)=>`<circle cx="${X(i).toFixed(1)}" cy="${Y(s.get(r)).toFixed(1)}" r="2.6" fill="${s.color}"/>`).join("");
      });
      // hover columns
      let hov="";
      rows.forEach((r,i)=>{ const x0=i===0?P.l:(X(i-1)+X(i))/2, x1=i===n-1?W-P.r:(X(i)+X(i+1))/2;
        const lines=cfg.series.map(s=>`<span style="color:${s.color}">●</span> ${esc(s.label)}: <b>${esc(yFmt(s.get(r)))}</b>`).join("<br>");
        const tip=`<b>${esc(cfg.x?cfg.x(r):"")}</b><br>${lines}`;
        hov+=`<rect x="${x0}" y="${P.t}" width="${Math.max(1,x1-x0)}" height="${ih}" fill="transparent" data-tip="${esc(tip)}"/>`; });
      return `<svg viewBox="0 0 ${W} ${H}" width="100%" preserveAspectRatio="xMidYMid meet"><defs>${defs}</defs>${grid}${markers}${body}${hov}${xl}</svg>`;
    },

    legend(series){ return `<div class="chart-legend">`+series.map(s=>`<span class="lg"><span class="dot" style="background:${s.color}"></span>${esc(s.label)}</span>`).join("")+`</div>`; },

    // horizontal bars → html string. rows:[{name,value,label}], max optional
    hbars(rows, max){
      if(!rows||!rows.length) return `<div class="empty">Keine Daten.</div>`;
      const mx=max||Math.max(...rows.map(r=>r.value))||1;
      return rows.map(r=>`<div class="hbar"><div class="name">${esc(r.name)}</div>
        <div class="track"><div class="f" style="width:${Math.max(2,r.value/mx*100)}%"></div></div>
        <div class="val">${esc(r.label!=null?r.label:r.value)}</div></div>`).join("");
    },

    /* ---------- auth + sidebar boot ---------- */
    async _checkAuth(){ try{ const r=await fetch("/api/cockpit/auth",{headers:this.hdr()}); return (await r.json()).authed; }catch(e){ return false; } },
    async _login(){
      const pw=document.getElementById("pw").value, el=document.getElementById("loginErr"); el.textContent="";
      let r; try{ r=await fetch("/api/cockpit/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({password:pw})}); }catch(e){ el.textContent="Netzwerkfehler"; return; }
      if(r.ok){ document.getElementById("loginOverlay").classList.remove("show"); this._authed=true; if(this._readyFn)this._readyFn(); }
      else { el.textContent="Falsches Passwort"; document.getElementById("pw").value=""; }
    },
    async _logout(){ try{ await fetch("/api/cockpit/logout",{method:"POST",headers:this.hdr()}); }catch(e){} location.reload(); },

    _buildSidebar(){
      const page=document.body.dataset.page||"";
      const side=document.getElementById("sidebar"); if(!side)return;
      side.innerHTML =
        `<div class="brand"><span class="logo">${ICONS.bolt}</span><span><b>automatisierbar</b></span></div>`+
        `<nav class="nav">`+NAV.map(it=>{
          const key=this.apiKey?`?key=${encodeURIComponent(this.apiKey)}`:"";
          return `<a class="nav-item${it.page===page?" active":""}" data-page="${it.page}" href="${it.href}${key}">${it.icon}<span>${it.label}</span>${it.live?'<span class="live-dot"></span>':""}</a>`;
        }).join("")+`</nav>`+
        `<div class="sidebar-foot">
          <div class="budget-mini"><div class="bm-top"><span class="k">Budget</span><span class="v" id="bmVal">– / – CHF</span></div>
            <div class="gauge" id="bmGauge"><div class="fill" id="bmFill" style="width:0%"></div></div></div>
          <button class="logout" onclick="Shell._logout()">${ICONS.logout}<span>Logout</span></button>
        </div>`;
    },

    _injectOverlays(){
      if(!document.getElementById("toast")){ const t=document.createElement("div"); t.id="toast"; document.body.appendChild(t); }
      if(!document.getElementById("loginOverlay")){
        const o=document.createElement("div"); o.className="overlay"; o.id="loginOverlay";
        o.innerHTML=`<div class="modal" style="max-width:340px;text-align:center">
          <div style="font-weight:600;font-size:16px;margin-bottom:4px">🔒 Cockpit-Login</div>
          <div class="sub muted" style="margin-bottom:16px;font-size:13px">Bitte Passwort eingeben</div>
          <input id="pw" type="password" placeholder="Passwort" autocomplete="current-password" style="margin-bottom:12px" onkeydown="if(event.key==='Enter')Shell._login()">
          <button class="btn-primary" style="width:100%;justify-content:center" onclick="Shell._login()">Login</button>
          <div id="loginErr" class="sub" style="color:#fca5a5;margin-top:10px;min-height:16px;font-size:13px"></div></div>`;
        document.body.appendChild(o);
      }
      // shared chart tooltip + delegation
      if(!document.getElementById("chartTip")){
        const tip=document.createElement("div"); tip.id="chartTip"; tip.className="tip"; document.body.appendChild(tip);
        document.addEventListener("mouseover",e=>{ const t=e.target.closest&&e.target.closest("[data-tip]"); if(!t)return; tip.innerHTML=t.getAttribute("data-tip"); tip.classList.add("show"); });
        document.addEventListener("mousemove",e=>{ if(!tip.classList.contains("show"))return; const o=12; let x=e.clientX+o,y=e.clientY+o; const r=tip.getBoundingClientRect(); if(x+r.width>innerWidth)x=e.clientX-r.width-o; if(y+r.height>innerHeight)y=e.clientY-r.height-o; tip.style.left=x+"px"; tip.style.top=y+"px"; });
        document.addEventListener("mouseout",e=>{ if(e.target.closest&&e.target.closest("[data-tip]"))tip.classList.remove("show"); });
      }
    },

    async _loadBudget(){
      try{ const r=await fetch("/api/cockpit/budget",{headers:this.hdr()}); if(!r.ok)return; const d=await r.json();
        if(d && d.cap_chf!=null) this.budget(d.spent_chf||0, d.cap_chf); }catch(e){}
    },

    async boot(){
      this._buildSidebar();
      this._injectOverlays();
      if(this.apiKey || await this._checkAuth()){ this._authed=true; this._loadBudget(); if(this._readyFn)this._readyFn(); }
      else { document.getElementById("loginOverlay").classList.add("show"); const pw=document.getElementById("pw"); if(pw)pw.focus(); }
    },
  };

  window.Shell = Shell;
  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",()=>Shell.boot());
  else Shell.boot();
})();
