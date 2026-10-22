# Worker

This small online service receives findings from a local monitoring
program. It asks Gemini to write a plain explanation and a suggested
fix, then saves the finding. It also gives a reporting page one
address from which to retrieve findings.

These steps connect a Cloudflare account and a Google AI Studio
account.

## Step one, get a Gemini key

Go to Google AI Studio and get an API key. Keep it somewhere safe for
step four.

## Step two, install the tools

From inside this `worker` folder, run this.

```
npm install
```

If asked to log in to Cloudflare, follow the prompt in the browser
window that opens.

## Step three, create the database

```
npx wrangler d1 create kvm-monitor-db
```

This prints out a database ID. Copy it into `wrangler.toml`, replacing
where it says REPLACE_WITH_YOUR_DATABASE_ID.

Then create the table.

```
npx wrangler d1 execute kvm-monitor-db --file=schema.sql --remote
```

## Step four, save the Gemini key as a secret

```
npx wrangler secret put GEMINI_API_KEY
```

It will ask you to paste the key from step one. This keeps the key on
Cloudflare's side rather than in a file that might be shared.

## Step five, deploy

```
npx wrangler deploy
```

This prints out your worker's address, such as
`https://YOUR_WORKER_NAME.YOUR_ACCOUNT_NAME.workers.dev`.

## Step six, connect the local program

Open `monitor/cloud_sender.py` and replace the placeholder address at
the top with your worker address, followed by `/report-anomaly`.

## What the reporting page needs

The reporting page can retrieve the full list of findings with a
request to your worker address followed by `/anomalies`.
