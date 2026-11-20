# User guide: business card in your own brand

[Deutsche Version](anleitung.md) · [Back to overview](../README.en.md)

This guide shows you step by step how to create a business card with the skill. It takes about 10 minutes.

## 1. One-time setup

1. Put the folder into your agent's skill folder:
   - Claude Code: `~/.claude/skills/business-card`
   - Codex: `~/.codex/skills/business-card`
2. Run `uv sync` in that folder. Without `uv`, use `python3 -m pip install segno==1.6.6`.
3. For PNG and PDF, install `rsvg-convert`:
   - macOS: `brew install librsvg`
   - Linux: `apt install librsvg2-bin`

## 2. What you need

- **Your LinkedIn profile URL.** You find it in your profile under *Contact info*, for example `linkedin.com/in/your-name`.
- **Your profile data**, in one of these ways:
  - Type your name, headline, company and location into the chat.
  - Or save your profile as a PDF: Profile → *More* → *Save to PDF*.
  - Or use the LinkedIn data export: *Settings* → *Data privacy* → *Get a copy of your data*.
- **Your website**, so the skill can detect colours, fonts and logo. Without a website, a primary colour and a logo file are enough.
- Optional: a **photo**, square, at least 600 × 600 pixels.

## 3. Ask for your card

Tell your agent something like this:

> Create a business card from my LinkedIn profile in the style of https://my-company.com. Profile URL: linkedin.com/in/my-name. Show email and website, no phone number. I need a print file. Use English labels.

The agent then does the following:

1. It reads your profile and your website's brand.
2. It shows you the detected colours, fonts and logo.
3. It renders all layouts as a gallery and picks the best fit.
4. It checks readability, text length and the QR code.
5. It hands you the files and the instructions for the LinkedIn app.

## 4. Check the result

- Open `preview.html` and look at both sides.
- Scan the QR code with your phone. It must open your LinkedIn profile.
- Read the notes in `report.json`. They tell you, for example, whether a font was replaced or a text was shortened.

## 5. Print

- Send `card-print.pdf` to your printer. The size is 85 × 55 mm, and 3 mm bleed is already included.
- Order rounded corners from your printer as a separate finishing option.
- Make a test print and test the QR code first.

## 6. Set up the LinkedIn Business Card

LinkedIn only lets you design the card in the mobile app. The skill cannot fill it in for you. Open `linkedin-native-card.md` and follow the steps:

1. In the LinkedIn app, tap your profile photo in the top left, then tap the QR code.
2. Tap *Edit*. Choose *Info*, *Layout*, *Font*, *Colors*, *Pattern* and *Stickers and Doodle* as the instructions recommend.
3. Tap *Save*, then *Add to Wallet*.

Good to know: swapping cards by scanning does **not** send a connection request. Connect with the person afterwards.

## What the skill does not promise

- Detected colours, fonts and logos are suggestions. Check them.
- Print results are not guaranteed. Make a test print.
- Information about the LinkedIn feature reflects the state of 20 November 2026 and may change.
