/**
 * This is my small online service. It has two jobs.
 *
 * One, when my local program finds something unusual, it sends that
 * finding here. I ask Gemini to write a plain explanation and a
 * suggested fix, then I save the whole thing.
 *
 * Two, I let the reporting page pull the full list of findings from
 * one simple address, so that page never needs to know how any of
 * this works underneath.
 */

const GEMINI_MODEL = "gemini-3.5-flash-lite";
const GEMINI_URL = `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent`;

function withCors(response) {
  response.headers.set("Access-Control-Allow-Origin", "*");
  response.headers.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  response.headers.set("Access-Control-Allow-Headers", "Content-Type");
  return response;
}

async function askGeminiForExplanation(env, finding) {
  const prompt =
    `I am watching a computer and my program just flagged something as unusual. ` +
    `The reading was for ${finding.metric}, and the value was ${finding.value}. ` +
    `I marked the severity as ${finding.severity}. ` +
    `In plain, simple words, with no technical terms, explain what this likely means ` +
    `and give one clear suggestion for what to check or do next. ` +
    `Keep it short, two or three sentences at most. ` +
    `Answer with the explanation first, then a line that starts with Suggested fix.`;

  const body = {
    contents: [{ parts: [{ text: prompt }] }],
  };

  const res = await fetch(`${GEMINI_URL}?key=${env.GEMINI_API_KEY}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const errorText = await res.text();
    return {
      explanation: "I could not reach the explanation service right now.",
      suggested_fix: "Check this finding by hand for now.",
      raw_error: `status ${res.status}: ${errorText}`,
    };
  }

  const data = await res.json();
  const text = data.candidates?.[0]?.content?.parts?.[0]?.text || "";

  const splitPoint = text.toLowerCase().indexOf("suggested fix");
  let explanation = text;
  let suggestedFix = "";
  if (splitPoint !== -1) {
    explanation = text.slice(0, splitPoint).trim();
    suggestedFix = text.slice(splitPoint).replace(/suggested fix:?/i, "").trim();
  }

  return { explanation, suggested_fix: suggestedFix };
}

async function handleReportAnomaly(request, env) {
  const finding = await request.json();

  if (!finding.metric || finding.value === undefined) {
    return withCors(new Response(JSON.stringify({ ok: false, error: "metric and value are required" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    }));
  }

  const { explanation, suggested_fix, raw_error } = await askGeminiForExplanation(env, finding);
  const timestamp = finding.timestamp || Date.now() / 1000;

  await env.DB.prepare(
    "INSERT INTO anomalies (timestamp, metric, value, severity, explanation, suggested_fix) VALUES (?, ?, ?, ?, ?, ?)"
  )
    .bind(timestamp, finding.metric, finding.value, finding.severity || "medium", explanation, suggested_fix)
    .run();

  return withCors(new Response(JSON.stringify({ ok: true, explanation, suggested_fix, raw_error }), {
    headers: { "Content-Type": "application/json" },
  }));
}

async function handleGetAnomalies(env) {
  const { results } = await env.DB.prepare(
    "SELECT id, timestamp, metric, value, severity, explanation, suggested_fix FROM anomalies ORDER BY timestamp DESC LIMIT 100"
  ).all();

  return withCors(new Response(JSON.stringify(results), {
    headers: { "Content-Type": "application/json" },
  }));
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return withCors(new Response(null, { status: 204 }));
    }

    if (url.pathname === "/report-anomaly" && request.method === "POST") {
      return handleReportAnomaly(request, env);
    }

    if (url.pathname === "/anomalies" && request.method === "GET") {
      return handleGetAnomalies(env);
    }

    return withCors(new Response("Not found", { status: 404 }));
  },
};