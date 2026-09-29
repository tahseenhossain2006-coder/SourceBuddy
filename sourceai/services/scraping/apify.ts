const APIFY_TOKEN = process.env.APIFY_TOKEN;

export async function scrapeWithApify(url: string): Promise<string | null> {
  if (!APIFY_TOKEN) return null;
  try {
    const runRes = await fetch('https://api.apify.com/v2/acts/aYwB7rJZneRArHv7a/runs', {
      method: 'POST',
      headers: { Authorization: `Bearer ${APIFY_TOKEN}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        startUrls: [{ url }],
        maxDepth: 1,
        maxPages: 1,
        extractOutputFunction: `async ({ html }) => { return { html }; }`,
      }),
    });
    const runData = await runRes.json();
    const runId = runData.data?.id;
    if (!runId) return null;

    for (let i = 0; i < 15; i++) {
      await new Promise(r => setTimeout(r, 2000));
      const statusRes = await fetch(`https://api.apify.com/v2/actor-runs/${runId}`, {
        headers: { Authorization: `Bearer ${APIFY_TOKEN}` },
      });
      const status = await statusRes.json();
      if (status.data?.status === 'SUCCEEDED') break;
      if (status.data?.status === 'FAILED') return null;
    }
    const datasetRes = await fetch(`https://api.apify.com/v2/actor-runs/${runId}/dataset/items`, {
      headers: { Authorization: `Bearer ${APIFY_TOKEN}` },
    });
    const items = await datasetRes.json();
    if (items && items[0]?.html) return items[0].html;
    return null;
  } catch {
    return null;
  }
}