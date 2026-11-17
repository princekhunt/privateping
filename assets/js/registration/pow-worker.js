"use strict";

function leadingZeroBits(bytes) {
  let count = 0;
  for (let i = 0; i < bytes.length; i++) {
    const b = bytes[i];
    if (b === 0) { count += 8; continue; }
    return count + Math.clz32(b) - 24;
  }
  return count;
}

self.onmessage = async function (e) {
  const challenge = e.data.challenge;
  const bits = e.data.bits;
  const enc = new TextEncoder();
  const BATCH = 2000;
  let nonce = 0;
  let lastReport = 0;
  for (;;) {
    const jobs = [];
    for (let i = 0; i < BATCH; i++) {
      jobs.push(crypto.subtle.digest("SHA-256", enc.encode(challenge + ":" + (nonce + i))));
    }
    const digests = await Promise.all(jobs);
    for (let i = 0; i < BATCH; i++) {
      if (leadingZeroBits(new Uint8Array(digests[i])) >= bits) {
        self.postMessage({ done: true, nonce: String(nonce + i), tried: nonce + i + 1 });
        return;
      }
    }
    nonce += BATCH;
    if (nonce - lastReport >= 10000) {
      lastReport = nonce;
      self.postMessage({ done: false, tried: nonce });
    }
  }
};
