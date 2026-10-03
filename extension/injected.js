/**
 * Injected into the page's MAIN world on flow.google.com — has access to
 * window.grecaptcha and the hijack bypass state from hijack_bypass.js.
 *
 * reCAPTCHA minting strategy (v0.5.1):
 *
 *   1. PRISTINE path (preferred): hijack_bypass.js captured the real execute
 *      function before Flow's x2a trap overwrote it. We call it directly with
 *      our own action — the token is clean.
 *
 *   2. OBJECT.ASSIGN NEUTER (fallback): we lost the race (all three trap levels
 *      + ready + poll missed). x2a's wrapper uses Object.assign to inject the
 *      poison action. We temporarily replace Object.assign during the execute
 *      call: if the result contains action:"extension_hijack_detected", we
 *      restore the real action before it reaches the original execute function.
 *
 *   3. WIDGET path (legacy fallback): if neither bypass is available, fall back
 *      to the pre-bypass render+execute approach. This WILL be trapped, but
 *      provides graceful degradation with a clear error message.
 */
const SITE_KEY = '6LdsFiUsAAAAAIjVDZcuLhaHiDn5nnHVXVRQGeMV';

// ─── TRPC Response Monitor ─────────────────────────────────
// Monkey-patch fetch to intercept TRPC responses containing media URLs.
// Fresh signed GCS URLs are extracted and forwarded to the agent.

const _originalFetch = window.fetch;
window.fetch = async function (...args) {
  const response = await _originalFetch.apply(this, args);
  try {
    const url = typeof args[0] === 'string' ? args[0] : args[0]?.url || '';
    // Only intercept TRPC calls on labs.google that return project/flow data
    if (url.includes('/fx/api/trpc/') && response.ok) {
      const clone = response.clone();
      clone.text().then(text => {
        if (text.includes('flow-content.google/') || text.includes('storage.googleapis.com/')) {
          window.dispatchEvent(new CustomEvent('TRPC_MEDIA_URLS', {
            detail: { url, body: text },
          }));
        }
      }).catch(() => {});
    }
  } catch {}
  return response;
};


let captchaMintTail = Promise.resolve();

// ─── Site key resolution ────────────────────────────────────
// Prefer the site key the page is currently configured with; the constant is
// only a fallback for a page that has not configured one yet.

function resolveSitekey() {
  try {
    const cfg = window.___grecaptcha_cfg || {};
    const clients = cfg.clients || {};
    for (const k of Object.keys(clients)) {
      const c = clients[k];
      if (c && c.sitekey) return c.sitekey;
    }
  } catch (e) { /* fall through to the constant */ }
  return SITE_KEY;
}

function waitReady(timeout = 5000) {
  return new Promise((resolve) => {
    let done = false;
    const fin = () => { if (!done) { done = true; resolve(); } };
    try { window.grecaptcha?.enterprise?.ready?.(fin); } catch (e) { /* ignore */ }
    setTimeout(fin, timeout);
  });
}

// ─── Bypass: Object.assign neuter ───────────────────────────
// Last-resort fallback when hijack_bypass.js couldn't capture the pristine
// execute. x2a's wrapper does:
//   c.execute = (e, f) => d(e, Object.assign({}, f, { action: "extension_hijack_detected" }))
// We temporarily replace Object.assign so the poison action is stripped before
// it reaches the real execute function `d`.

const _realObjectAssign = Object.assign;

async function executeWithAssignNeuter(target, action) {
  const targetAction = action;

  Object.assign = function (dest, ...sources) {
    const result = _realObjectAssign.call(this, dest, ...sources);
    if (result && typeof result === 'object' &&
        result.action === 'extension_hijack_detected') {
      result.action = targetAction;
    }
    return result;
  };

  try {
    await waitReady(2500);
    const token = await Promise.race([
      window.grecaptcha.enterprise.execute(target, { action }),
      new Promise((_, rej) => setTimeout(() => rej(new Error('execute_hang')), 8000)),
    ]);
    return token ? String(token) : null;
  } finally {
    Object.assign = _realObjectAssign;
  }
}

// ─── Bypass: pristine execute (primary path) ────────────────

async function executeWithPristine(target, action) {
  const pristine = window.__fk_hijack?.pristine;
  if (typeof pristine !== 'function') return null;
  const token = await Promise.race([
    pristine(target, { action }),
    new Promise((_, rej) => setTimeout(() => rej(new Error('execute_hang')), 8000)),
  ]);
  return token ? String(token) : null;
}

// ─── Widget resolution / initialization ────────────────────

let _widgetPromise = null;
function ensureWidget(sitekey) {
  if (_widgetPromise) return _widgetPromise;
  _widgetPromise = (async () => {
    await waitReady(5000);
    // Reuse existing client if one already exists in grecaptcha cfg
    try {
      const cfg = window.___grecaptcha_cfg || {};
      const clients = cfg.clients || {};
      for (const k of Object.keys(clients)) {
        const c = clients[k];
        if (c && (c.sitekey === sitekey || !sitekey)) {
          return isNaN(k) ? k : Number(k);
        }
      }
    } catch (e) { /* ignore */ }

    let host = document.getElementById('flowkit-recaptcha-host');
    if (!host) {
      host = document.createElement('div');
      host.id = 'flowkit-recaptcha-host';
      host.style.cssText = 'position:fixed;left:-9999px;top:0;width:1px;height:1px;';
      (document.body || document.documentElement).appendChild(host);
    }
    return await new Promise((resolve, reject) => {
      try {
        const widgetId = window.grecaptcha.enterprise.render(host, {
          sitekey,
          size: 'invisible',
          callback: () => {},
          'error-callback': (m) => reject(new Error('render_error: ' + m)),
        });
        resolve(widgetId);
      } catch (e) {
        reject(new Error('render_threw: ' + (e && e.message || e)));
      }
    });
  })().catch((e) => { _widgetPromise = null; throw e; });
  return _widgetPromise;
}

// ─── Unified mint with retry ────────────────────────────────

let _lastBypassUsed = null;

async function executeWithRetry(sitekey, action, attempts = 2) {
  let lastErr = null;
  const hijack = window.__fk_hijack;
  const hasPristine = typeof hijack?.pristine === 'function';
  const knownTrapped = !!hijack?.trapped;

  for (let i = 0; i < attempts; i++) {
    try {
      await waitReady(2500);
      let target = sitekey;
      try {
        const widgetId = await ensureWidget(sitekey);
        if (widgetId !== null && widgetId !== undefined) {
          target = widgetId;
        }
      } catch (errWidget) {
        console.warn('[FlowKit] ensureWidget failed, falling back to sitekey:', errWidget);
      }

      // Path 1: pristine execute captured by hijack_bypass.js
      if (hasPristine) {
        try {
          const token = await executeWithPristine(target, action);
          if (token) {
            _lastBypassUsed = `pristine(${hijack.source || 'unknown'})`;
            return token;
          }
          lastErr = new Error('pristine_empty_token');
        } catch (e1) {
          lastErr = e1;
          console.warn('[FlowKit] pristine execute failed:', e1);
        }
      }

      // Path 2: Object.assign neuter (we know the trap is active or pristine failed)
      if (knownTrapped || !hasPristine || lastErr) {
        try {
          const token = await executeWithAssignNeuter(target, action);
          if (token) {
            _lastBypassUsed = 'assign_neuter';
            return token;
          }
          lastErr = new Error('assign_neuter_empty_token');
        } catch (e2) {
          lastErr = e2;
          console.warn('[FlowKit] assign neuter failed:', e2);
        }
      }

      // Path 3: legacy widget / direct execute
      const token = await Promise.race([
        window.grecaptcha.enterprise.execute(target, { action }),
        new Promise((_, rej) => setTimeout(() => rej(new Error('execute_hang')), 8000)),
      ]);
      if (token) {
        _lastBypassUsed = 'legacy_widget';
        return String(token);
      }
      lastErr = new Error('empty_token');
    } catch (e) {
      lastErr = e;
    }
    await new Promise((r) => setTimeout(r, 600));
  }
  throw lastErr || new Error('execute_failed');
}

async function mintCaptcha(pageAction) {
  const previous = captchaMintTail.catch(() => {});
  let release;
  captchaMintTail = new Promise((resolve) => { release = resolve; });
  await previous;
  try {
    await waitForGrecaptcha();
    return await executeWithRetry(resolveSitekey(), pageAction);
  } finally {
    release();
  }
}

window.addEventListener('GET_CAPTCHA', async ({ detail }) => {
  const { requestId, pageAction } = detail;
  try {
    const token = await mintCaptcha(pageAction);
    const hijack = window.__fk_hijack;
    window.dispatchEvent(new CustomEvent('CAPTCHA_RESULT', {
      detail: {
        requestId,
        token,
        // Diagnostic: tell the agent which path was used
        bypassPath: _lastBypassUsed || (typeof hijack?.pristine === 'function'
          ? `pristine(${hijack.source})`
          : hijack?.trapped ? 'assign_neuter' : 'legacy_widget'),
      },
    }));
  } catch (e) {
    window.dispatchEvent(new CustomEvent('CAPTCHA_RESULT', {
      detail: { requestId, error: e.message },
    }));
  }
});

function waitForGrecaptcha(timeout = 22000) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const check = () => {
      // If render is available and either pristine or execute is ready
      if (window.grecaptcha?.enterprise?.render && (window.__fk_hijack?.pristine || window.grecaptcha?.enterprise?.execute)) {
        return resolve();
      }
      if (Date.now() - start > timeout) {
        if (window.__fk_hijack?.pristine || window.grecaptcha?.enterprise?.execute) return resolve();
        return reject(new Error('grecaptcha not available'));
      }
      setTimeout(check, 200);
    };
    check();
  });
}
