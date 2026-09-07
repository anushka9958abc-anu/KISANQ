import Redis from "ioredis";

const REDIS_URL = process.env.REDIS_URL || "redis://localhost:6379/0";
const CHANNEL = process.env.NOTIFY_CHANNEL || "kisanq.notifications";

const redis = new Redis(REDIS_URL);

function sendSms(payload) {
  const host = process.env.SMPP_HOST;
  if (!host) {
    console.log(`[SMS mock] to=${payload.phone} :: ${payload.message}`);
    return;
  }
  console.log(`[SMPP] bind ${host}:${process.env.SMPP_PORT || 2775} -> ${payload.phone}`);
}

function sendWhatsApp(payload) {
  if (!process.env.WHATSAPP_TOKEN) {
    console.log(`[WhatsApp mock] to=${payload.phone} :: ${payload.message}`);
    return;
  }
  console.log(`[WhatsApp Cloud API] ${payload.phone} :: ${payload.title}`);
}

function sendIvrHint(payload) {
  console.log(`[Asterisk IVR queue] farmer ${payload.phone} can dial 1800-KISANQ for token status`);
}

redis.subscribe(CHANNEL, (err) => {
  if (err) {
    console.error("Redis subscribe failed", err);
    process.exit(1);
  }
  console.log(`KISANQ notification worker listening on ${CHANNEL}`);
});

redis.on("message", (_channel, raw) => {
  try {
    const payload = JSON.parse(raw);
    if (payload.channel === "sms") sendSms(payload);
    else if (payload.channel === "whatsapp") sendWhatsApp(payload);
    else sendIvrHint(payload);
  } catch (e) {
    console.error("Bad notification payload", e);
  }
});
