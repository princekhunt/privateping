(function (global) {
  "use strict";

  const DB_NAME = "privateping";
  const STORE = "identity";
  const KEY_ID = "self";
  const RSA_PARAMS = {
    name: "RSA-OAEP",
    modulusLength: 2048,
    publicExponent: new Uint8Array([0x01, 0x00, 0x01]),
    hash: "SHA-256",
  };
  const RSA_IMPORT = { name: "RSA-OAEP", hash: "SHA-256" };
  const EC_PARAMS = { name: "ECDSA", namedCurve: "P-256" };
  const EC_SIGN = { name: "ECDSA", hash: "SHA-256" };
  const VERSION = 2;
  const MAX_CLOCK_SKEW_MS = 10 * 60 * 1000;

  const te = new TextEncoder();
  const td = new TextDecoder();
  const subtle = global.crypto && global.crypto.subtle;

  function b64(bytes) {
    bytes = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
    let bin = "";
    for (let i = 0; i < bytes.length; i += 0x8000) {
      bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    }
    return btoa(bin);
  }

  function unb64(str) {
    if (typeof str !== "string") throw new Error("bad base64");
    const bin = atob(str);
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }

  function concat() {
    const parts = Array.prototype.map.call(arguments, (p) => (p instanceof Uint8Array ? p : new Uint8Array(p)));
    const out = new Uint8Array(parts.reduce((n, p) => n + p.length, 0));
    let off = 0;
    parts.forEach((p) => { out.set(p, off); off += p.length; });
    return out;
  }

  function randomId() {
    return Array.from(global.crypto.getRandomValues(new Uint8Array(16)))
      .map((b) => b.toString(16).padStart(2, "0")).join("");
  }

  function openDb() {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, 1);
      req.onupgradeneeded = () => req.result.createObjectStore(STORE);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }

  async function tx(mode, op) {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const t = db.transaction(STORE, mode);
      const req = op(t.objectStore(STORE));
      t.oncomplete = () => { db.close(); resolve(req ? req.result : undefined); };
      t.onerror = t.onabort = () => { db.close(); reject(t.error); };
    });
  }

  function loadIdentity() {
    return tx("readonly", (s) => s.get(KEY_ID)).then((v) => v || null);
  }

  function saveIdentity(identity) {
    return tx("readwrite", (s) => s.put(identity, KEY_ID));
  }

  async function wipe() {
    try { localStorage.removeItem("privateKey"); } catch (e) {  }
    try { await tx("readwrite", (s) => s.clear()); } catch (e) {  }
  }

  async function generateIdentity() {
    if (!subtle || !global.indexedDB) throw new Error("This browser does not support secure key storage.");

    const encPair = await subtle.generateKey(RSA_PARAMS, false, ["encrypt", "decrypt"]);
    const sigPair = await subtle.generateKey(EC_PARAMS, false, ["sign", "verify"]);
    const encPublic = await subtle.exportKey("jwk", encPair.publicKey);
    const sigPublic = await subtle.exportKey("jwk", sigPair.publicKey);
    await wipe();
    await saveIdentity({
      encPrivate: encPair.privateKey,
      sigPrivate: sigPair.privateKey,
      encPublic: encPublic,
      sigPublic: sigPublic,
      created: Date.now(),
    });
    return { encPublic: encPublic, sigPublic: sigPublic };
  }

  function importPeer(keys) {
    if (!keys || !keys.enc || !keys.sig) return Promise.reject(new Error("missing peer keys"));
    return Promise.all([
      subtle.importKey("jwk", keys.enc, RSA_IMPORT, false, ["encrypt"]),
      subtle.importKey("jwk", keys.sig, EC_PARAMS, false, ["verify"]),
    ]).then((r) => ({ enc: r[0], sig: r[1] }));
  }

  function canonical(encJwk, sigJwk) {
    return "RSA:" + encJwk.n + ":" + encJwk.e + "|EC:" + sigJwk.crv + ":" + sigJwk.x + ":" + sigJwk.y;
  }

  function sameKeys(a, b) {
    return !!(a && b && a.enc && a.sig && b.enc && b.sig &&
      canonical(a.enc, a.sig) === canonical(b.enc, b.sig));
  }

  async function safetyCode(userA, keysA, userB, keysB) {
    const parts = [[userA, canonical(keysA.enc, keysA.sig)], [userB, canonical(keysB.enc, keysB.sig)]]
      .sort((x, y) => (x[0] < y[0] ? -1 : 1))
      .map((p) => p[0] + "=" + p[1]);
    const digest = new Uint8Array(await subtle.digest("SHA-512", te.encode("pp-safety-v1|" + parts.join("|"))));
    const view = new DataView(digest.buffer);
    const groups = [];
    for (let i = 0; i < 12; i++) groups.push(String(view.getUint32(i * 4) % 100000).padStart(5, "0"));
    return groups.join(" ");
  }

  async function seal(body, me, to, peer, identity, id) {
    const envelope = JSON.stringify({ from: me, to: to, ts: Date.now(), id: id || randomId(), body: String(body) });
    const aesKey = await subtle.generateKey({ name: "AES-GCM", length: 256 }, true, ["encrypt"]);
    const rawAes = await subtle.exportKey("raw", aesKey);
    const iv = global.crypto.getRandomValues(new Uint8Array(12));
    const c = new Uint8Array(await subtle.encrypt({ name: "AES-GCM", iv: iv }, aesKey, te.encode(envelope)));
    const k = new Uint8Array(await subtle.encrypt({ name: "RSA-OAEP" }, peer.enc, rawAes));
    const s = new Uint8Array(await subtle.sign(EC_SIGN, identity.sigPrivate, concat(te.encode("pp-v2"), k, iv, c)));
    return JSON.stringify({ v: VERSION, k: b64(k), iv: b64(iv), c: b64(c), s: b64(s) });
  }

  const seen = new Set();

  async function open(wire, me, from, peer, identity, mid) {
    const msg = JSON.parse(wire);
    if (!msg || msg.v !== VERSION) throw new Error("unsupported message version");
    const k = unb64(msg.k), iv = unb64(msg.iv), c = unb64(msg.c), s = unb64(msg.s);
    if (iv.length !== 12) throw new Error("bad iv");

    const ok = await subtle.verify(EC_SIGN, peer.sig, s, concat(te.encode("pp-v2"), k, iv, c));
    if (!ok) throw new Error("signature check failed");

    const rawAes = await subtle.decrypt({ name: "RSA-OAEP" }, identity.encPrivate, k);
    const aesKey = await subtle.importKey("raw", rawAes, { name: "AES-GCM" }, false, ["decrypt"]);
    const envelope = JSON.parse(td.decode(await subtle.decrypt({ name: "AES-GCM", iv: iv }, aesKey, c)));

    if (!envelope || envelope.from !== from || envelope.to !== me) throw new Error("message not meant for this chat");
    if (typeof envelope.ts !== "number" || Math.abs(Date.now() - envelope.ts) > MAX_CLOCK_SKEW_MS) {
      throw new Error("stale message");
    }
    if (typeof envelope.id !== "string" || !/^[0-9a-f]{32}$/.test(envelope.id)) throw new Error("bad id");

    if (mid !== undefined && mid !== envelope.id) throw new Error("id mismatch");
    if (typeof envelope.body !== "string") throw new Error("bad body");
    envelope.duplicate = seen.has(envelope.id);
    seen.add(envelope.id);
    return envelope;
  }

  const RECEIPT_STATES = ["delivered", "read"];

  async function signReceipt(state, ids, me, to, identity) {
    const r = JSON.stringify({ v: 1, state: state, ids: ids, from: me, to: to, ts: Date.now() });
    const s = new Uint8Array(await subtle.sign(EC_SIGN, identity.sigPrivate, te.encode("pp-receipt-v1|" + r)));
    return JSON.stringify({ r: r, s: b64(s) });
  }

  async function verifyReceipt(wire, me, from, peer) {
    const outer = JSON.parse(wire);
    if (!outer || typeof outer.r !== "string" || typeof outer.s !== "string") throw new Error("bad receipt");
    const ok = await subtle.verify(EC_SIGN, peer.sig, unb64(outer.s), te.encode("pp-receipt-v1|" + outer.r));
    if (!ok) throw new Error("receipt signature check failed");
    const r = JSON.parse(outer.r);
    if (!r || r.v !== 1 || r.from !== from || r.to !== me) throw new Error("receipt not for this chat");
    if (RECEIPT_STATES.indexOf(r.state) === -1 || !Array.isArray(r.ids)) throw new Error("bad receipt");
    if (typeof r.ts !== "number" || Math.abs(Date.now() - r.ts) > MAX_CLOCK_SKEW_MS) throw new Error("stale receipt");
    return { state: r.state, ids: r.ids.filter((id) => typeof id === "string" && /^[0-9a-f]{32}$/.test(id)) };
  }

  global.PPCrypto = {
    generateIdentity: generateIdentity,
    loadIdentity: loadIdentity,
    wipe: wipe,
    importPeer: importPeer,
    safetyCode: safetyCode,
    sameKeys: sameKeys,
    seal: seal,
    open: open,
    newId: randomId,
    signReceipt: signReceipt,
    verifyReceipt: verifyReceipt,
  };
})(window);
