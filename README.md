# Kuro Bot

a silly discord bot for voting to send people to the padded room. made for a specific server.

## commands

- **`/vote @member`** - start a vote to send someone to the padded room
  - Users react with 👍 (yes) or 👎 (no) to vote
  - 60-second vote window
  - If yes wins, the member gets the padded room role for 5 minutes
  - 15-minute cooldown between votes per user
- **`/ping`** - check the bot's latency
- **`/github`** - get the link to the bot's GitHub repo

## easter eggs

say these in chat and the bot will reply:

- `quack` 🦆
- `meow` 🐱
- `woof` 🐶

## sticker detection

if someone uses a specific sticker, the bot will ping a role. users can be banned from using the sticker via `banned_ids.json`.

## invite

https://discord.gg/MhBG6fgPmS
