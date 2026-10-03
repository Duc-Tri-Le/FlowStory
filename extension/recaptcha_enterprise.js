/**
 * recaptcha_enterprise.js — Pre-configuration for reCAPTCHA Enterprise
 *
 * Injected in MAIN world at document_start via manifest.json.
 * Sets up window.___grecaptcha_cfg before recaptcha__en.js runs.
 *
 * NOTE: Do NOT create any <script> tag here — recaptcha__en.js is already
 * loaded as a content_script in manifest.json, and flow.google.com's CSP
 * enforces require-trusted-types-for 'script' which blocks dynamic script tags.
 */
(function () {
  var w = window, C = '___grecaptcha_cfg', cfg = w[C] = w[C] || {}, N = 'grecaptcha';
  var E = 'enterprise', a = w[N] = w[N] || {}, gr = a[E] = a[E] || {};
  gr.ready = gr.ready || function (f) { (cfg['fns'] = cfg['fns'] || []).push(f); };
  w['__recaptcha_api'] = 'https://www.google.com/recaptcha/enterprise/';
  (cfg['enterprise'] = cfg['enterprise'] || []).push(true);
  (cfg['render'] = cfg['render'] || []).push('explicit');
  (cfg['anchor-ms'] = cfg['anchor-ms'] || []).push(20000);
  (cfg['execute-ms'] = cfg['execute-ms'] || []).push(30000);
  w['__google_recaptcha_client'] = true;
})();