/**
 * Qubia Widget v1
 * Uso:
 *   <script src="https://cdn.qubia.es/widget/v1.js"
 *           data-qubia-key="qb_pub_slug_xxxx"
 *           data-api="https://api.qubia.es"></script>
 */
(function () {
  "use strict";

  var script = document.currentScript;
  var KEY = script.getAttribute("data-qubia-key");
  var API = (script.getAttribute("data-api") || "https://api.qubia.es").replace(/\/$/, "");
  var POS = script.getAttribute("data-position") || "right";

  if (!KEY) {
    console.error("[Qubia] Falta data-qubia-key");
    return;
  }

  var NEGRO = "#0E0C09";
  var TEAL = "#2DD4BF";
  var PIEDRA = "#8A8578";

  var sessionId = (function () {
    var k = "qubia_session";
    var v = null;
    try {
      v = sessionStorage.getItem(k);
    } catch (e) {}
    if (!v) {
      v = "s_" + Math.random().toString(36).slice(2) + Date.now().toString(36);
      try {
        sessionStorage.setItem(k, v);
      } catch (e) {}
    }
    return v;
  })();

  var config = { nombre_asistente: "Asistente", saludo_inicial: "Hola, ¿en qué puedo ayudarte?", leads_activo: false };
  var abierto = false;
  var enviando = false;
  var leadMostrado = false;

  // ---------------------------------------------------------------- estilos
  var css =
    ".qb-root{position:fixed;bottom:20px;" + POS + ":20px;z-index:2147483000;" +
    "font-family:'Plus Jakarta Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}" +
    ".qb-btn{width:56px;height:56px;border-radius:50%;border:none;cursor:pointer;" +
    "background:" + NEGRO + ";color:" + TEAL + ";display:flex;align-items:center;" +
    "justify-content:center;box-shadow:0 4px 20px rgba(0,0,0,.28);transition:transform .18s ease;}" +
    ".qb-btn:hover{transform:scale(1.06);}" +
    ".qb-panel{position:absolute;bottom:70px;" + POS + ":0;width:360px;max-width:calc(100vw - 40px);" +
    "height:520px;max-height:calc(100vh - 120px);background:" + NEGRO + ";border-radius:3px;" +
    "box-shadow:0 12px 48px rgba(0,0,0,.4);display:none;flex-direction:column;overflow:hidden;}" +
    ".qb-panel.qb-open{display:flex;}" +
    ".qb-head{padding:16px 18px;border-bottom:1px solid rgba(138,133,120,.22);flex-shrink:0;}" +
    ".qb-head-t{color:#fff;font-size:15px;font-weight:600;}" +
    ".qb-head-s{color:" + PIEDRA + ";font-size:11px;letter-spacing:1.6px;margin-top:2px;}" +
    ".qb-body{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:10px;}" +
    ".qb-msg{max-width:82%;padding:10px 13px;border-radius:3px;font-size:14px;line-height:1.5;" +
    "white-space:pre-wrap;word-wrap:break-word;}" +
    ".qb-msg-bot{background:rgba(255,255,255,.06);color:#f0efec;align-self:flex-start;}" +
    ".qb-msg-user{background:" + TEAL + ";color:" + NEGRO + ";align-self:flex-end;font-weight:500;}" +
    ".qb-dots{display:flex;gap:4px;padding:12px 13px;align-self:flex-start;}" +
    ".qb-dot{width:6px;height:6px;border-radius:50%;background:" + PIEDRA + ";animation:qbb 1.3s infinite;}" +
    ".qb-dot:nth-child(2){animation-delay:.16s}.qb-dot:nth-child(3){animation-delay:.32s}" +
    "@keyframes qbb{0%,60%,100%{opacity:.28}30%{opacity:1}}" +
    ".qb-foot{padding:12px;border-top:1px solid rgba(138,133,120,.22);display:flex;gap:8px;flex-shrink:0;}" +
    ".qb-input{flex:1;background:rgba(255,255,255,.06);border:1px solid transparent;border-radius:3px;" +
    "padding:10px 12px;color:#fff;font-size:14px;outline:none;font-family:inherit;}" +
    ".qb-input:focus{border-color:" + TEAL + ";}" +
    ".qb-input::placeholder{color:" + PIEDRA + ";}" +
    ".qb-send{background:" + TEAL + ";color:" + NEGRO + ";border:none;border-radius:3px;" +
    "padding:0 15px;cursor:pointer;font-weight:600;font-size:14px;font-family:inherit;}" +
    ".qb-send:disabled{opacity:.45;cursor:not-allowed;}" +
    ".qb-lead{background:rgba(45,212,191,.08);border:1px solid rgba(45,212,191,.28);" +
    "border-radius:3px;padding:13px;display:flex;flex-direction:column;gap:8px;}" +
    ".qb-lead-t{color:" + TEAL + ";font-size:12px;font-weight:600;}" +
    ".qb-lead input{background:rgba(255,255,255,.06);border:1px solid transparent;border-radius:3px;" +
    "padding:8px 10px;color:#fff;font-size:13px;outline:none;font-family:inherit;}" +
    ".qb-lead input:focus{border-color:" + TEAL + ";}" +
    ".qb-lead input::placeholder{color:" + PIEDRA + ";}" +
    ".qb-lead button{background:" + TEAL + ";color:" + NEGRO + ";border:none;border-radius:3px;" +
    "padding:9px;cursor:pointer;font-weight:600;font-size:13px;font-family:inherit;}" +
    ".qb-note{color:" + PIEDRA + ";font-size:12px;text-align:center;}" +
    "@media(max-width:480px){.qb-panel{width:calc(100vw - 32px);height:calc(100vh - 110px);}}";

  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  // ------------------------------------------------------------------- DOM
  var root = document.createElement("div");
  root.className = "qb-root";
  root.innerHTML =
    '<div class="qb-panel" role="dialog" aria-label="Asistente virtual">' +
    '<div class="qb-head"><div class="qb-head-t"></div><div class="qb-head-s">QUBIA</div></div>' +
    '<div class="qb-body"></div>' +
    '<div class="qb-foot">' +
    '<input class="qb-input" type="text" placeholder="Escribe tu mensaje..." maxlength="2000" aria-label="Mensaje">' +
    '<button class="qb-send" type="button">Enviar</button>' +
    "</div></div>" +
    '<button class="qb-btn" type="button" aria-label="Abrir asistente">' +
    '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">' +
    '<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="9" ry="3.6"/><path d="M12 3v18"/>' +
    "</svg></button>";
  document.body.appendChild(root);

  var panel = root.querySelector(".qb-panel");
  var body = root.querySelector(".qb-body");
  var input = root.querySelector(".qb-input");
  var sendBtn = root.querySelector(".qb-send");
  var toggleBtn = root.querySelector(".qb-btn");
  var titulo = root.querySelector(".qb-head-t");

  // -------------------------------------------------------------- helpers
  function scrollAbajo() {
    body.scrollTop = body.scrollHeight;
  }

  function addMsg(texto, quien) {
    var d = document.createElement("div");
    d.className = "qb-msg qb-msg-" + quien;
    d.textContent = texto;
    body.appendChild(d);
    scrollAbajo();
  }

  function mostrarDots() {
    var d = document.createElement("div");
    d.className = "qb-dots";
    d.innerHTML = '<div class="qb-dot"></div><div class="qb-dot"></div><div class="qb-dot"></div>';
    body.appendChild(d);
    scrollAbajo();
    return d;
  }

  function api(ruta, payload) {
    return fetch(API + ruta, {
      method: payload ? "POST" : "GET",
      headers: { "Content-Type": "application/json", "X-Qubia-Key": KEY },
      body: payload ? JSON.stringify(payload) : undefined
    }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    });
  }

  function mostrarFormularioLead() {
    if (leadMostrado || !config.leads_activo) return;
    leadMostrado = true;

    var box = document.createElement("div");
    box.className = "qb-lead";
    box.innerHTML =
      '<div class="qb-lead-t">Déjanos tus datos y te contactamos</div>' +
      '<input type="text" placeholder="Nombre" data-f="nombre">' +
      '<input type="tel" placeholder="Teléfono" data-f="telefono">' +
      '<input type="email" placeholder="Email (opcional)" data-f="email">' +
      "<button type=\"button\">Enviar</button>";
    body.appendChild(box);
    scrollAbajo();

    box.querySelector("button").addEventListener("click", function () {
      var datos = { session_id: sessionId, motivo: "Solicitado desde el chat" };
      var campos = box.querySelectorAll("input");
      for (var i = 0; i < campos.length; i++) {
        datos[campos[i].getAttribute("data-f")] = campos[i].value.trim();
      }
      if (!datos.nombre || !datos.telefono) {
        addMsg("Necesito al menos tu nombre y teléfono.", "bot");
        return;
      }
      box.remove();
      api("/v1/lead", datos)
        .then(function (r) {
          var n = document.createElement("div");
          n.className = "qb-note";
          n.textContent = r.mensaje || "Gracias, te contactamos en breve.";
          body.appendChild(n);
          scrollAbajo();
        })
        .catch(function () {
          addMsg("No he podido enviar tus datos. Inténtalo de nuevo.", "bot");
          leadMostrado = false;
        });
    });
  }

  function enviar() {
    var texto = input.value.trim();
    if (!texto || enviando) return;

    enviando = true;
    sendBtn.disabled = true;
    addMsg(texto, "user");
    input.value = "";
    var dots = mostrarDots();

    api("/v1/chat", { session_id: sessionId, mensaje: texto })
      .then(function (r) {
        dots.remove();
        addMsg(r.respuesta, "bot");
        if (r.sugerir_lead) setTimeout(mostrarFormularioLead, 500);
      })
      .catch(function () {
        dots.remove();
        addMsg("Ahora mismo no puedo responder. Inténtalo en un momento.", "bot");
      })
      .then(function () {
        enviando = false;
        sendBtn.disabled = false;
        input.focus();
      });
  }

  // -------------------------------------------------------------- eventos
  toggleBtn.addEventListener("click", function () {
    abierto = !abierto;
    panel.classList.toggle("qb-open", abierto);
    if (abierto) {
      input.focus();
      scrollAbajo();
    }
  });

  sendBtn.addEventListener("click", enviar);
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter") enviar();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && abierto) toggleBtn.click();
  });

  // --------------------------------------------------------------- inicio
  api("/v1/config")
    .then(function (c) {
      config = c;
      titulo.textContent = c.nombre_asistente || "Asistente";
      addMsg(c.saludo_inicial || "Hola, ¿en qué puedo ayudarte?", "bot");
    })
    .catch(function () {
      titulo.textContent = "Asistente";
      addMsg("Hola, ¿en qué puedo ayudarte?", "bot");
    });
})();
