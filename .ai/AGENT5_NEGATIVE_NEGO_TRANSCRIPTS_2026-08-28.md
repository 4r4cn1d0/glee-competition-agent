# Agent 5 negative negotiation transcripts after restart

Snapshot and scope:

- Agent: Agent 5 (local fleet slot composite).
- Restart boundary: Aug 28, 2026 6:26:32 PM IST; replacement PID 36072.
- Dashboard snapshot: through Aug 28, 2026 7:10 PM IST.
- Completed post-restart negotiation games visible in the snapshot: 85.
- Games with a displayed negative rating: 44 of 85.
- Negative cards by role: 20 buyer, 24 seller.
- Negative cards by outcome: 21 agreements, 20 no-deals, 3 walk-aways.
- Sum of displayed negative deltas: -238.6; this is descriptive, not a causal strategy estimate.
- Transcript records below: 625 server-history rows across 44 games.
- Dashboard-to-local-evidence join: 44/44 unique matches; 0 unresolved; 0 ambiguous. Ratings were excluded from the transcript fingerprint used for matching.
- The latest nine joins comprised three exact completed-modal fingerprints and six exact live-turn-prefix matches at join time; all nine final local game files were present before this report was finalized.
- Ordering: newest dashboard card first.

Each transcript row reproduces the server history: the offerer, price, optional message, responder decision, and any counteroffer. Because the server records the counteroffer again as the next round's offer, adjacent rows intentionally repeat that price.

<details>
<summary>1. Aug 28, 2026 7:10 PM — Seller, No deal, rating -5.9</summary>

- Game ID: f613d5e4-cba1-407b-b766-72f4f695b1b4
- Opponent: AGENT_SUMMERS (agent)
- Evidence source: completed local game log, uniquely joined to the authenticated dashboard card.
- Setup: our value $12,000; opponent value hidden; incomplete information; horizon 10; messages not allowed.
- Result: No deal; our payoff $0; opponent payoff $0; rounds played 10.

Transcript:

- R1: Us (Seller) offered $47,647.2. Opponent (Buyer) rejected; counteroffered $12,000.
- R2: Opponent (Buyer) offered $12,000. Us (Seller) rejected; counteroffered $46,588.8.
- R3: Us (Seller) offered $46,588.8. Opponent (Buyer) rejected; counteroffered $12,000.
- R4: Opponent (Buyer) offered $12,000. Us (Seller) rejected; counteroffered $42,355.2.
- R5: Us (Seller) offered $42,355.2. Opponent (Buyer) rejected; counteroffered $12,000.
- R6: Opponent (Buyer) offered $12,000. Us (Seller) rejected; counteroffered $35,299.2.
- R7: Us (Seller) offered $35,299.2. Opponent (Buyer) rejected; counteroffered $12,000.
- R8: Opponent (Buyer) offered $12,000. Us (Seller) rejected; counteroffered $14,000.
- R9: Us (Seller) offered $14,000. Opponent (Buyer) rejected; counteroffered $12,000.
- R10: Opponent (Buyer) offered $12,000. Us (Seller) rejected.

</details>

<details>
<summary>2. Aug 28, 2026 7:10 PM — Seller, No deal, rating -8.7</summary>

- Game ID: 858c0d0e-5dd4-4b7d-b4e7-3cd4a35a50b9
- Opponent: Yosef Zoabi (human)
- Evidence source: completed local game log, uniquely joined to the authenticated dashboard card.
- Setup: our value $800,000; opponent value $1,200,000; complete information; horizon 1; messages not allowed.
- Result: No deal; our payoff $0; opponent payoff $0; rounds played 1.

Transcript:

- R1: Us (Seller) offered $1,199,999.99. Opponent (Buyer) rejected.

</details>

<details>
<summary>3. Aug 28, 2026 7:09 PM — Buyer, Agreement, rating -6.1</summary>

- Game ID: f9c8e662-47e4-42a5-889e-9a7a5760e352
- Opponent: grok 4.6 (agent)
- Evidence source: completed local game log, uniquely joined to the authenticated dashboard card.
- Setup: our value $1,500,000; opponent value $1,200,000; complete information; horizon 1; messages not allowed.
- Result: Agreement; our payoff $3,000; opponent payoff $297,000; rounds played 1.
- Agreement: price $1,497,000 on round 1.

Transcript:

- R1: Opponent (Seller) offered $1,497,000. Us (Buyer) accepted.

</details>

<details>
<summary>4. Aug 28, 2026 7:08 PM — Seller, Walked away, rating -1.3</summary>

- Game ID: b4a2c450-9cf7-4fc9-b12c-063725124570
- Opponent: hidden/undisclosed (hidden)
- Evidence source: completed local game log, uniquely joined to the authenticated dashboard card.
- Setup: our value $1,000,000; opponent value hidden; incomplete information; horizon 10; messages not allowed.
- Result: Walked away; our payoff $0; opponent payoff $0; rounds played 1.

Transcript:

- R1: Us (Seller) offered $3,970,600. Opponent (Buyer) walked away.

</details>

<details>
<summary>5. Aug 28, 2026 7:08 PM — Buyer, Agreement, rating -8.1</summary>

- Game ID: 541fceaf-da07-409c-bc13-9da158611d3c
- Opponent: DonYoshi (agent)
- Evidence source: completed local game log, uniquely joined to the authenticated dashboard card.
- Setup: our value $1,500,000; opponent value hidden; incomplete information; horizon 1; messages allowed.
- Result: Agreement; our payoff $300,000; opponent payoff $400,000; rounds played 1.
- Agreement: price $1,200,000 on round 1.

Transcript:

- R1: Opponent (Seller) offered $1,200,000. Message: “I propose the stated price of 1200000.” Us (Buyer) accepted.

</details>

<details>
<summary>6. Aug 28, 2026 7:08 PM — Seller, No deal, rating -1.4</summary>

- Game ID: 6e8ed910-8284-4c8a-a493-1ed1b51041fa
- Opponent: hidden/undisclosed (hidden)
- Evidence source: completed local game log, uniquely joined to the authenticated dashboard card.
- Setup: our value $15,000; opponent value hidden; incomplete information; horizon 1; messages not allowed.
- Result: No deal; our payoff $0; opponent payoff $0; rounds played 1.

Transcript:

- R1: Us (Seller) offered $20,000. Opponent (Buyer) rejected.

</details>

<details>
<summary>7. Aug 28, 2026 7:05 PM — Buyer, No deal, rating -8.6</summary>

- Game ID: dcb590bc-ee00-49dd-83b9-ff4808c09b0f
- Opponent: hidden/undisclosed (hidden)
- Evidence source: completed local game log, uniquely joined to the authenticated dashboard card.
- Setup: our value $150; opponent value $120; complete information; horizon unknown (observed 95 history rows); messages allowed.
- Result: No deal; our payoff $0; opponent payoff $0; rounds played 95.

Transcript:

- R1: Opponent (Seller) offered $148.8. Message: “That is my price for this one. I would rather close now than trade rounds -- tell me if it works.” Us (Buyer) rejected; counteroffered $121.2.
- R2: Us (Buyer) offered $121.2. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $147.87.
- R3: Opponent (Seller) offered $147.87. Message: “Below my line, but here is a number I can actually sign.” Us (Buyer) rejected; counteroffered $123.06.
- R4: Us (Buyer) offered $123.06. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $146.01.
- R5: Opponent (Seller) offered $146.01. Message: “Below my line, but here is a number I can actually sign.” Us (Buyer) rejected; counteroffered $124.92.
- R6: Us (Buyer) offered $124.92. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $144.15.
- R7: Opponent (Seller) offered $144.15. Message: “Below my line, but here is a number I can actually sign.” Us (Buyer) rejected; counteroffered $126.78.
- R8: Us (Buyer) offered $126.78. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $142.29.
- R9: Opponent (Seller) offered $142.29. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R10: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $140.43.
- R11: Opponent (Seller) offered $140.43. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R12: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R13: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R14: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R15: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R16: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R17: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R18: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R19: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R20: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R21: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R22: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R23: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R24: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R25: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R26: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R27: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R28: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R29: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R30: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R31: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R32: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R33: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R34: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R35: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R36: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R37: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R38: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R39: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R40: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R41: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R42: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R43: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R44: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R45: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R46: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R47: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R48: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R49: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R50: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R51: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R52: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R53: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R54: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R55: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R56: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R57: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R58: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R59: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R60: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R61: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R62: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R63: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R64: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R65: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R66: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R67: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R68: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R69: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R70: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R71: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R72: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R73: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R74: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R75: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R76: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R77: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R78: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R79: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R80: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R81: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R82: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R83: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R84: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R85: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R86: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R87: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R88: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R89: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R90: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R91: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R92: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R93: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.
- R94: Us (Buyer) offered $128.64. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $139.5.
- R95: Opponent (Seller) offered $139.5. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Buyer) rejected; counteroffered $128.64.

</details>

<details>
<summary>8. Aug 28, 2026 7:02 PM — Buyer, Agreement, rating -7.9</summary>

- Game ID: b12fdab9-412a-488e-8049-2d8fff4645bd
- Opponent: AK_four (agent)
- Evidence source: completed local game log, uniquely joined to the authenticated dashboard card.
- Setup: our value $150; opponent value hidden; incomplete information; horizon unknown (observed 10 history rows); messages not allowed.
- Result: Agreement; our payoff $25.5; opponent payoff $44.5; rounds played 10.
- Agreement: price $124.5 on round 10.

Transcript:

- R1: Opponent (Seller) offered $141. Us (Buyer) rejected; counteroffered $90.5.
- R2: Us (Buyer) offered $90.5. Opponent (Seller) rejected; counteroffered $141.
- R3: Opponent (Seller) offered $141. Us (Buyer) rejected; counteroffered $90.5.
- R4: Us (Buyer) offered $90.5. Opponent (Seller) rejected; counteroffered $141.
- R5: Opponent (Seller) offered $141. Us (Buyer) rejected; counteroffered $107.5.
- R6: Us (Buyer) offered $107.5. Opponent (Seller) rejected; counteroffered $141.
- R7: Opponent (Seller) offered $141. Us (Buyer) rejected; counteroffered $107.5.
- R8: Us (Buyer) offered $107.5. Opponent (Seller) rejected; counteroffered $141.
- R9: Opponent (Seller) offered $141. Us (Buyer) rejected; counteroffered $124.5.
- R10: Us (Buyer) offered $124.5. Opponent (Seller) accepted.

</details>

<details>
<summary>9. Aug 28, 2026 7:01 PM — Buyer, No deal, rating -8.7</summary>

- Game ID: 9af82c85-28e5-4372-8356-e8a1ea64dc91
- Opponent: hidden/undisclosed (hidden)
- Evidence source: completed local game log, uniquely joined to the authenticated dashboard card.
- Setup: our value $1,500,000; opponent value $1,000,000; complete information; horizon unknown (observed 97 history rows); messages not allowed.
- Result: No deal; our payoff $0; opponent payoff $0; rounds played 97.

Transcript:

- R1: Opponent (Seller) offered $1,450,000. Us (Buyer) rejected; counteroffered $1,020,000.
- R2: Us (Buyer) offered $1,020,000. Opponent (Seller) rejected; counteroffered $1,425,000.
- R3: Opponent (Seller) offered $1,425,000. Us (Buyer) rejected; counteroffered $1,051,000.
- R4: Us (Buyer) offered $1,051,000. Opponent (Seller) rejected; counteroffered $1,375,000.
- R5: Opponent (Seller) offered $1,375,000. Us (Buyer) rejected; counteroffered $1,082,000.
- R6: Us (Buyer) offered $1,082,000. Opponent (Seller) rejected; counteroffered $1,325,000.
- R7: Opponent (Seller) offered $1,325,000. Us (Buyer) rejected; counteroffered $1,113,000.
- R8: Us (Buyer) offered $1,113,000. Opponent (Seller) rejected; counteroffered $1,275,000.
- R9: Opponent (Seller) offered $1,275,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R10: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R11: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R12: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R13: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R14: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R15: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R16: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R17: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R18: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R19: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R20: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R21: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R22: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R23: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R24: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R25: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R26: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R27: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R28: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R29: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R30: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R31: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R32: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R33: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R34: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R35: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R36: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R37: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R38: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R39: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R40: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R41: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R42: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R43: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R44: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R45: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R46: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R47: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R48: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R49: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R50: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R51: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R52: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R53: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R54: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R55: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R56: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R57: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R58: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R59: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R60: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R61: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R62: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R63: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R64: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R65: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R66: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R67: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R68: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R69: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R70: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R71: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R72: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R73: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R74: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R75: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R76: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R77: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R78: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R79: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R80: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R81: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R82: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R83: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R84: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R85: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R86: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R87: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R88: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R89: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R90: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R91: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R92: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R93: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R94: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R95: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.
- R96: Us (Buyer) offered $1,144,000. Opponent (Seller) rejected; counteroffered $1,250,000.
- R97: Opponent (Seller) offered $1,250,000. Us (Buyer) rejected; counteroffered $1,144,000.

</details>

<details>
<summary>10. Aug 28, 2026 7:00 PM — Seller, Agreement, rating -6.0</summary>

- Game ID: 9cabf008-f502-449d-9d3b-a3730cfc73df
- Opponent: hidden/undisclosed (hidden)
- Setup: our value $80; opponent value hidden; incomplete information; horizon unknown (observed 88 history rows); messages not allowed.
- Result: Agreement; our payoff $2.4; opponent payoff $17.6; rounds played 88.
- Agreement: price $82.4 on round 88.

Transcript:

- R1: Us (Seller) offered $317.65. Opponent (Buyer) rejected; counteroffered $67.67.
- R2: Opponent (Buyer) offered $67.67. Us (Seller) rejected; counteroffered $310.59.
- R3: Us (Seller) offered $310.59. Opponent (Buyer) rejected; counteroffered $67.67.
- R4: Opponent (Buyer) offered $67.67. Us (Seller) rejected; counteroffered $282.37.
- R5: Us (Seller) offered $282.37. Opponent (Buyer) rejected; counteroffered $67.67.
- R6: Opponent (Buyer) offered $67.67. Us (Seller) rejected; counteroffered $235.33.
- R7: Us (Seller) offered $235.33. Opponent (Buyer) rejected; counteroffered $67.67.
- R8: Opponent (Buyer) offered $67.67. Us (Seller) rejected; counteroffered $90.
- R9: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $67.67.
- R10: Opponent (Buyer) offered $67.67. Us (Seller) rejected; counteroffered $90.
- R11: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $67.67.
- R12: Opponent (Buyer) offered $67.67. Us (Seller) rejected; counteroffered $90.
- R13: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $67.67.
- R14: Opponent (Buyer) offered $67.67. Us (Seller) rejected; counteroffered $90.
- R15: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $67.67.
- R16: Opponent (Buyer) offered $67.67. Us (Seller) rejected; counteroffered $90.
- R17: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $67.68.
- R18: Opponent (Buyer) offered $67.68. Us (Seller) rejected; counteroffered $90.
- R19: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $67.69.
- R20: Opponent (Buyer) offered $67.69. Us (Seller) rejected; counteroffered $90.
- R21: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $67.7.
- R22: Opponent (Buyer) offered $67.7. Us (Seller) rejected; counteroffered $90.
- R23: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $67.71.
- R24: Opponent (Buyer) offered $67.71. Us (Seller) rejected; counteroffered $90.
- R25: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $67.73.
- R26: Opponent (Buyer) offered $67.73. Us (Seller) rejected; counteroffered $90.
- R27: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $67.75.
- R28: Opponent (Buyer) offered $67.75. Us (Seller) rejected; counteroffered $90.
- R29: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $67.78.
- R30: Opponent (Buyer) offered $67.78. Us (Seller) rejected; counteroffered $90.
- R31: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $67.81.
- R32: Opponent (Buyer) offered $67.81. Us (Seller) rejected; counteroffered $90.
- R33: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $67.86.
- R34: Opponent (Buyer) offered $67.86. Us (Seller) rejected; counteroffered $90.
- R35: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $67.91.
- R36: Opponent (Buyer) offered $67.91. Us (Seller) rejected; counteroffered $90.
- R37: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $67.97.
- R38: Opponent (Buyer) offered $67.97. Us (Seller) rejected; counteroffered $90.
- R39: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $68.05.
- R40: Opponent (Buyer) offered $68.05. Us (Seller) rejected; counteroffered $90.
- R41: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $68.13.
- R42: Opponent (Buyer) offered $68.13. Us (Seller) rejected; counteroffered $90.
- R43: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $68.23.
- R44: Opponent (Buyer) offered $68.23. Us (Seller) rejected; counteroffered $90.
- R45: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $68.35.
- R46: Opponent (Buyer) offered $68.35. Us (Seller) rejected; counteroffered $90.
- R47: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $68.48.
- R48: Opponent (Buyer) offered $68.48. Us (Seller) rejected; counteroffered $90.
- R49: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $68.63.
- R50: Opponent (Buyer) offered $68.63. Us (Seller) rejected; counteroffered $90.
- R51: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $68.8.
- R52: Opponent (Buyer) offered $68.8. Us (Seller) rejected; counteroffered $90.
- R53: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $68.99.
- R54: Opponent (Buyer) offered $68.99. Us (Seller) rejected; counteroffered $90.
- R55: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $69.21.
- R56: Opponent (Buyer) offered $69.21. Us (Seller) rejected; counteroffered $90.
- R57: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $69.45.
- R58: Opponent (Buyer) offered $69.45. Us (Seller) rejected; counteroffered $90.
- R59: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $69.72.
- R60: Opponent (Buyer) offered $69.72. Us (Seller) rejected; counteroffered $90.
- R61: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $70.02.
- R62: Opponent (Buyer) offered $70.02. Us (Seller) rejected; counteroffered $90.
- R63: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $70.35.
- R64: Opponent (Buyer) offered $70.35. Us (Seller) rejected; counteroffered $90.
- R65: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $70.71.
- R66: Opponent (Buyer) offered $70.71. Us (Seller) rejected; counteroffered $90.
- R67: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $71.11.
- R68: Opponent (Buyer) offered $71.11. Us (Seller) rejected; counteroffered $90.
- R69: Us (Seller) offered $90. Opponent (Buyer) rejected; counteroffered $71.55.
- R70: Opponent (Buyer) offered $71.55. Us (Seller) rejected; counteroffered $150.07.
- R71: Us (Seller) offered $150.07. Opponent (Buyer) rejected; counteroffered $72.03.
- R72: Opponent (Buyer) offered $72.03. Us (Seller) rejected; counteroffered $150.07.
- R73: Us (Seller) offered $150.07. Opponent (Buyer) rejected; counteroffered $72.55.
- R74: Opponent (Buyer) offered $72.55. Us (Seller) rejected; counteroffered $150.07.
- R75: Us (Seller) offered $150.07. Opponent (Buyer) rejected; counteroffered $73.11.
- R76: Opponent (Buyer) offered $73.11. Us (Seller) rejected; counteroffered $150.07.
- R77: Us (Seller) offered $150.07. Opponent (Buyer) rejected; counteroffered $73.73.
- R78: Opponent (Buyer) offered $73.73. Us (Seller) rejected; counteroffered $150.07.
- R79: Us (Seller) offered $150.07. Opponent (Buyer) rejected; counteroffered $74.39.
- R80: Opponent (Buyer) offered $74.39. Us (Seller) rejected; counteroffered $150.07.
- R81: Us (Seller) offered $150.07. Opponent (Buyer) rejected; counteroffered $75.1.
- R82: Opponent (Buyer) offered $75.1. Us (Seller) rejected; counteroffered $150.07.
- R83: Us (Seller) offered $150.07. Opponent (Buyer) rejected; counteroffered $75.88.
- R84: Opponent (Buyer) offered $75.88. Us (Seller) rejected; counteroffered $150.07.
- R85: Us (Seller) offered $150.07. Opponent (Buyer) rejected; counteroffered $76.71.
- R86: Opponent (Buyer) offered $76.71. Us (Seller) rejected; counteroffered $150.07.
- R87: Us (Seller) offered $150.07. Opponent (Buyer) rejected; counteroffered $82.4.
- R88: Opponent (Buyer) offered $82.4. Us (Seller) accepted.

</details>

<details>
<summary>11. Aug 28, 2026 7:00 PM — Buyer, Agreement, rating -6.4</summary>

- Game ID: f7b79b21-a407-425c-b781-7cbf7d13720b
- Opponent: 7aidara_Alpha (agent)
- Setup: our value $150; opponent value hidden; incomplete information; horizon 1; messages not allowed.
- Result: Agreement; our payoff $0.01; opponent payoff $49.99; rounds played 1.
- Agreement: price $149.99 on round 1.

Transcript:

- R1: Opponent (Seller) offered $149.99. Us (Buyer) accepted.

</details>

<details>
<summary>12. Aug 28, 2026 7:00 PM — Buyer, Agreement, rating -5.6</summary>

- Game ID: 5028ce17-2160-4d59-9401-d48a5176f18b
- Opponent: hidden/undisclosed (hidden)
- Setup: our value $15,000; opponent value hidden; incomplete information; horizon unknown (observed 10 history rows); messages allowed.
- Result: Agreement; our payoff $2,550; opponent payoff $2,450; rounds played 10.
- Agreement: price $12,450 on round 10.

Transcript:

- R1: Opponent (Seller) offered $14,750. Message: “This price reflects what the item is worth to me; I have room to talk but not much.” Us (Buyer) rejected; counteroffered $9,050.
- R2: Us (Buyer) offered $9,050. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $14,731.03.
- R3: Opponent (Seller) offered $14,731.03. Message: “That&#x27;s a real move toward you. I&#x27;ve got very little left to give.” Us (Buyer) rejected; counteroffered $9,050.
- R4: Us (Buyer) offered $9,050. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $14,685.53.
- R5: Opponent (Seller) offered $14,685.53. Message: “That&#x27;s a real move toward you. I&#x27;ve got very little left to give.” Us (Buyer) rejected; counteroffered $10,750.
- R6: Us (Buyer) offered $10,750. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $14,406.31.
- R7: Opponent (Seller) offered $14,406.31. Message: “I&#x27;ve come down again — that&#x27;s another concession from me. We&#x27;re close; let&#x27;s finish it.” Us (Buyer) rejected; counteroffered $10,750.
- R8: Us (Buyer) offered $10,750. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $14,360.81.
- R9: Opponent (Seller) offered $14,360.81. Message: “That&#x27;s a real move toward you. I&#x27;ve got very little left to give.” Us (Buyer) rejected; counteroffered $12,450.
- R10: Us (Buyer) offered $12,450. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) accepted.

</details>

<details>
<summary>13. Aug 28, 2026 6:59 PM — Seller, Agreement, rating -6.4</summary>

- Game ID: 9bbb3f1a-1707-4d37-aacc-5dc2ef8cf814
- Opponent: 7aidara_Alpha (agent)
- Setup: our value $10,000; opponent value $15,000; complete information; horizon 10; messages allowed.
- Result: Agreement; our payoff $1,130; opponent payoff $3,870; rounds played 10.
- Agreement: price $11,130 on round 10.

Transcript:

- R1: Us (Seller) offered $14,750. Message: “That is my price for this one. I would rather close now than trade rounds -- tell me if it works.” Opponent (Buyer) rejected; counteroffered $10,200.
- R2: Opponent (Buyer) offered $10,200. Message: “Above what I can justify. Here is where I can go.” Us (Seller) rejected; counteroffered $14,000.
- R3: Us (Seller) offered $14,000. Message: “Below my line, but here is a number I can actually sign.” Opponent (Buyer) rejected; counteroffered $10,510.
- R4: Opponent (Buyer) offered $10,510. Message: “Above what I can justify. Here is where I can go.” Us (Seller) rejected; counteroffered $14,000.
- R5: Us (Seller) offered $14,000. Message: “Below my line, but here is a number I can actually sign.” Opponent (Buyer) rejected; counteroffered $10,820.
- R6: Opponent (Buyer) offered $10,820. Message: “Above what I can justify. Here is where I can go.” Us (Seller) rejected; counteroffered $14,000.
- R7: Us (Seller) offered $14,000. Message: “Below my line, but here is a number I can actually sign.” Opponent (Buyer) rejected; counteroffered $11,130.
- R8: Opponent (Buyer) offered $11,130. Message: “Above what I can justify. Here is where I can go.” Us (Seller) rejected; counteroffered $14,000.
- R9: Us (Seller) offered $14,000. Message: “I have moved as far as this is worth to me. Let us close here.” Opponent (Buyer) rejected; counteroffered $11,130.
- R10: Opponent (Buyer) offered $11,130. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Seller) accepted.

</details>

<details>
<summary>14. Aug 28, 2026 6:59 PM — Seller, Walked away, rating -1.5</summary>

- Game ID: c44f633a-0352-4b11-94d4-6d925d61061d
- Opponent: 7aidara (agent)
- Setup: our value $15,000; opponent value hidden; incomplete information; horizon 1; messages allowed.
- Result: Walked away; our payoff $0; opponent payoff $0; rounds played 1.

Transcript:

- R1: Us (Seller) offered $20,000. Opponent (Buyer) walked away.

</details>

<details>
<summary>15. Aug 28, 2026 6:56 PM — Buyer, No deal, rating -6.4</summary>

- Game ID: 24af7d52-60ed-4cf1-886d-15965adfbb52
- Opponent: 7aidara (agent)
- Setup: our value $1,000,000; opponent value hidden; incomplete information; horizon 1; messages allowed.
- Result: No deal; our payoff $0; opponent payoff $0; rounds played 1.

Transcript:

- R1: Opponent (Seller) offered $1,199,990. Message: “That is my price for this one. I would rather close now than trade rounds -- tell me if it works.” Us (Buyer) rejected.

</details>

<details>
<summary>16. Aug 28, 2026 6:55 PM — Buyer, No deal, rating -1.4</summary>

- Game ID: 0c2750de-d99a-405f-9d7c-a8f1ce49fee5
- Opponent: hidden/undisclosed (hidden)
- Setup: our value $12,000; opponent value hidden; incomplete information; horizon 1; messages allowed.
- Result: No deal; our payoff $0; opponent payoff $0; rounds played 1.

Transcript:

- R1: Opponent (Seller) offered $14,999.9. Message: “That is my price for this one. I would rather close now than trade rounds -- tell me if it works.” Us (Buyer) rejected.

</details>

<details>
<summary>17. Aug 28, 2026 6:54 PM — Seller, No deal, rating -2.8</summary>

- Game ID: 15cf3598-c0b0-4879-b54d-dd4681de7dd7
- Opponent: hidden/undisclosed (hidden)
- Setup: our value $1,200,000; opponent value hidden; incomplete information; horizon 1; messages not allowed.
- Result: No deal; our payoff $0; opponent payoff $0; rounds played 1.

Transcript:

- R1: Us (Seller) offered $1,499,999.99. Opponent (Buyer) rejected.

</details>

<details>
<summary>18. Aug 28, 2026 6:52 PM — Buyer, Agreement, rating -7.6</summary>

- Game ID: fb28db98-ad79-43c7-9b81-22f88f107b69
- Opponent: johnnie watcher (agent)
- Setup: our value $10,000; opponent value $8,000; complete information; horizon 1; messages allowed.
- Result: Agreement; our payoff $0.01; opponent payoff $1,999.99; rounds played 1.
- Agreement: price $9,999.99 on round 1.

Transcript:

- R1: Opponent (Seller) offered $9,999.99. Message: “if you will write my name I will accept whatever offer you will make. If it is hidden from you, write hidden, but I will only accept if you will discover my true name” Us (Buyer) accepted.

</details>

<details>
<summary>19. Aug 28, 2026 6:52 PM — Buyer, No deal, rating -1.4</summary>

- Game ID: 6b911541-3cc2-42b5-b924-6fa2b6865f65
- Opponent: Equilibrist (agent)
- Setup: our value $800,000; opponent value hidden; incomplete information; horizon 10; messages allowed.
- Result: No deal; our payoff $0; opponent payoff $0; rounds played 10.

Transcript:

- R1: Opponent (Seller) offered $1,719,608. Message: “Serious offer - priced so we both come out ahead. I can move a little, but this is the right neighborhood.” Us (Buyer) rejected; counteroffered $360,000.
- R2: Us (Buyer) offered $360,000. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $1,719,608.
- R3: Opponent (Seller) offered $1,719,608. Message: “Close, but not there yet - here&#x27;s a number that works for me.” Us (Buyer) rejected; counteroffered $471,508.
- R4: Us (Buyer) offered $471,508. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $1,441,176.
- R5: Opponent (Seller) offered $1,441,176. Message: “Close, but not there yet - here&#x27;s a number that works for me.” Us (Buyer) rejected; counteroffered $569,815.
- R6: Us (Buyer) offered $569,815. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $1,343,137.
- R7: Opponent (Seller) offered $1,343,137. Message: “Close, but not there yet - here&#x27;s a number that works for me.” Us (Buyer) rejected; counteroffered $652,831.
- R8: Us (Buyer) offered $652,831. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected; counteroffered $1,315,686.
- R9: Opponent (Seller) offered $1,315,686. Message: “Close, but not there yet - here&#x27;s a number that works for me.” Us (Buyer) rejected; counteroffered $716,938.
- R10: Us (Buyer) offered $716,938. Message: “Above what I can justify. Here is where I can go.” Opponent (Seller) rejected.

</details>

<details>
<summary>20. Aug 28, 2026 6:51 PM — Buyer, Agreement, rating -7.8</summary>

- Game ID: 0dab999a-fb7c-460d-947c-a35959c7adcb
- Opponent: johnnie watcher (agent)
- Setup: our value $1,500,000; opponent value $1,000,000; complete information; horizon 1; messages allowed.
- Result: Agreement; our payoff $0.01; opponent payoff $499,999.99; rounds played 1.
- Agreement: price $1,499,999.99 on round 1.

Transcript:

- R1: Opponent (Seller) offered $1,499,999.99. Message: “if you will write my name I will accept whatever offer you will make. If it is hidden from you, write hidden, but I will only accept if you will discover my true name” Us (Buyer) accepted.

</details>

<details>
<summary>21. Aug 28, 2026 6:49 PM — Buyer, No deal, rating -1.5</summary>

- Game ID: 15a1ec13-8430-48d0-9379-0c1b6e527fba
- Opponent: 7aidara (agent)
- Setup: our value $10,000; opponent value hidden; incomplete information; horizon 1; messages allowed.
- Result: No deal; our payoff $0; opponent payoff $0; rounds played 1.

Transcript:

- R1: Opponent (Seller) offered $28,500. Message: “That is my price for this one. I would rather close now than trade rounds -- tell me if it works.” Us (Buyer) rejected.

</details>

<details>
<summary>22. Aug 28, 2026 6:48 PM — Buyer, Agreement, rating -5.5</summary>

- Game ID: 94b1cb58-a692-4e1f-8f09-e9d63809104a
- Opponent: 7aidara_Beta (agent)
- Setup: our value $1,500,000; opponent value hidden; incomplete information; horizon 1; messages not allowed.
- Result: Agreement; our payoff $10; opponent payoff $299,990; rounds played 1.
- Agreement: price $1,499,990 on round 1.

Transcript:

- R1: Opponent (Seller) offered $1,499,990. Us (Buyer) accepted.

</details>

<details>
<summary>23. Aug 28, 2026 6:47 PM — Buyer, Agreement, rating -7.1</summary>

- Game ID: 18c46e03-415a-4ee9-926d-fb40d3a01f27
- Opponent: 7aidara_Beta (agent)
- Setup: our value $10,000; opponent value $8,000; complete information; horizon 1; messages not allowed.
- Result: Agreement; our payoff $0.1; opponent payoff $1,999.9; rounds played 1.
- Agreement: price $9,999.9 on round 1.

Transcript:

- R1: Opponent (Seller) offered $9,999.9. Us (Buyer) accepted.

</details>

<details>
<summary>24. Aug 28, 2026 6:46 PM — Seller, No deal, rating -1.5</summary>

- Game ID: cfb0594f-5999-4680-916f-622dcb5cabc3
- Opponent: hidden/undisclosed (hidden)
- Setup: our value $10,000; opponent value hidden; incomplete information; horizon 1; messages not allowed.
- Result: No deal; our payoff $0; opponent payoff $0; rounds played 1.

Transcript:

- R1: Us (Seller) offered $11,999.99. Opponent (Buyer) rejected.

</details>

<details>
<summary>25. Aug 28, 2026 6:46 PM — Seller, No deal, rating -8.9</summary>

- Game ID: 83c35d54-c598-4fd8-900d-aa3360f0f7db
- Opponent: 7aidara_Alpha (agent)
- Setup: our value $80; opponent value $120; complete information; horizon unknown (observed 96 history rows); messages not allowed.
- Result: No deal; our payoff $0; opponent payoff $0; rounds played 96.

Transcript:

- R1: Us (Seller) offered $118. Opponent (Buyer) rejected; counteroffered $81.6.
- R2: Opponent (Buyer) offered $81.6. Us (Seller) rejected; counteroffered $112.
- R3: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $84.08.
- R4: Opponent (Buyer) offered $84.08. Us (Seller) rejected; counteroffered $112.
- R5: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $86.56.
- R6: Opponent (Buyer) offered $86.56. Us (Seller) rejected; counteroffered $112.
- R7: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $89.04.
- R8: Opponent (Buyer) offered $89.04. Us (Seller) rejected; counteroffered $112.
- R9: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $91.52.
- R10: Opponent (Buyer) offered $91.52. Us (Seller) rejected; counteroffered $112.
- R11: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R12: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R13: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R14: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R15: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R16: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R17: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R18: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R19: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R20: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R21: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R22: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R23: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R24: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R25: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R26: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R27: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R28: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R29: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R30: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R31: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R32: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R33: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R34: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R35: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R36: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R37: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R38: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R39: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R40: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R41: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R42: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R43: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R44: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R45: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R46: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R47: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R48: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R49: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R50: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R51: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R52: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R53: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R54: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R55: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R56: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R57: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R58: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R59: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R60: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R61: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R62: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R63: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R64: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R65: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R66: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R67: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R68: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R69: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R70: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R71: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R72: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R73: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R74: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R75: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R76: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R77: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R78: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R79: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R80: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R81: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R82: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R83: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R84: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R85: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R86: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R87: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R88: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R89: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R90: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R91: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R92: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R93: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R94: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.
- R95: Us (Seller) offered $112. Opponent (Buyer) rejected; counteroffered $94.
- R96: Opponent (Buyer) offered $94. Us (Seller) rejected; counteroffered $112.

</details>

<details>
<summary>26. Aug 28, 2026 6:46 PM — Buyer, Agreement, rating -5.8</summary>

- Game ID: 2b8ff672-1c9f-4ef5-9181-73bb060bee22
- Opponent: hidden/undisclosed (hidden)
- Setup: our value $15,000; opponent value $8,000; complete information; horizon 1; messages not allowed.
- Result: Agreement; our payoff $280; opponent payoff $6,720; rounds played 1.
- Agreement: price $14,720 on round 1.

Transcript:

- R1: Opponent (Seller) offered $14,720. Us (Buyer) accepted.

</details>

<details>
<summary>27. Aug 28, 2026 6:45 PM — Buyer, No deal, rating -1.6</summary>

- Game ID: b2424f16-a41a-4d9a-a014-fa83db80666d
- Opponent: anchor (agent)
- Setup: our value $100; opponent value hidden; incomplete information; horizon 1; messages allowed.
- Result: No deal; our payoff $0; opponent payoff $0; rounds played 1.

Transcript:

- R1: Opponent (Seller) offered $200. Us (Buyer) rejected.

</details>

<details>
<summary>28. Aug 28, 2026 6:44 PM — Seller, Walked away, rating -1.5</summary>

- Game ID: b4b3d63f-6560-4a3e-95da-b99c23f32549
- Opponent: 7aidara_Gamma (agent)
- Setup: our value $120; opponent value hidden; incomplete information; horizon 1; messages not allowed.
- Result: Walked away; our payoff $0; opponent payoff $0; rounds played 1.

Transcript:

- R1: Us (Seller) offered $149.99. Opponent (Buyer) walked away.

</details>

<details>
<summary>29. Aug 28, 2026 6:44 PM — Seller, Agreement, rating -7.2</summary>

- Game ID: ecd76adf-0f22-4e0b-9aba-f36e20382731
- Opponent: hidden/undisclosed (hidden)
- Setup: our value $10,000; opponent value hidden; incomplete information; horizon unknown (observed 6 history rows); messages not allowed.
- Result: Agreement; our payoff $750; opponent payoff $4,250; rounds played 6.
- Agreement: price $10,750 on round 6.

Transcript:

- R1: Us (Seller) offered $39,706. Opponent (Buyer) rejected; counteroffered $9,050.
- R2: Opponent (Buyer) offered $9,050. Us (Seller) rejected; counteroffered $38,824.
- R3: Us (Seller) offered $38,824. Opponent (Buyer) rejected; counteroffered $9,050.
- R4: Opponent (Buyer) offered $9,050. Us (Seller) rejected; counteroffered $35,296.
- R5: Us (Seller) offered $35,296. Opponent (Buyer) rejected; counteroffered $10,750.
- R6: Opponent (Buyer) offered $10,750. Us (Seller) accepted.

</details>

<details>
<summary>30. Aug 28, 2026 6:44 PM — Seller, No deal, rating -4.9</summary>

- Game ID: f2aeccc7-4b9e-4d57-a0c5-59b7ccd15111
- Opponent: Guai (agent)
- Setup: our value $150; opponent value hidden; incomplete information; horizon 10; messages allowed.
- Result: No deal; our payoff $0; opponent payoff $0; rounds played 10.

Transcript:

- R1: Us (Seller) offered $595.73. Message: “That is my price for this one. I would rather close now than trade rounds -- tell me if it works.” Opponent (Buyer) rejected; counteroffered $78.
- R2: Opponent (Buyer) offered $78. Message: “A small adjustment can get us to agreement.” Us (Seller) rejected; counteroffered $582.9.
- R3: Us (Seller) offered $582.9. Message: “Below my line, but here is a number I can actually sign.” Opponent (Buyer) rejected; counteroffered $88.67.
- R4: Opponent (Buyer) offered $88.67. Message: “A small adjustment can get us to agreement.” Us (Seller) rejected; counteroffered $531.6.
- R5: Us (Seller) offered $531.6. Message: “Below my line, but here is a number I can actually sign.” Opponent (Buyer) rejected; counteroffered $99.33.
- R6: Opponent (Buyer) offered $99.33. Message: “A small adjustment can get us to agreement.” Us (Seller) rejected; counteroffered $446.1.
- R7: Us (Seller) offered $446.1. Message: “Below my line, but here is a number I can actually sign.” Opponent (Buyer) rejected; counteroffered $110.
- R8: Opponent (Buyer) offered $110. Message: “A small adjustment can get us to agreement.” Us (Seller) rejected; counteroffered $152.
- R9: Us (Seller) offered $152. Message: “I have moved as far as this is worth to me. Let us close here.” Opponent (Buyer) rejected; counteroffered $120.67.
- R10: Opponent (Buyer) offered $120.67. Message: “A small adjustment can get us to agreement.” Us (Seller) rejected.

</details>

<details>
<summary>31. Aug 28, 2026 6:41 PM — Seller, No deal, rating -1.5</summary>

- Game ID: 19827fcc-0f26-4060-b6be-902049ecb36f
- Opponent: hidden/undisclosed (hidden)
- Setup: our value $120; opponent value hidden; incomplete information; horizon 1; messages not allowed.
- Result: No deal; our payoff $0; opponent payoff $0; rounds played 1.

Transcript:

- R1: Us (Seller) offered $149.99. Opponent (Buyer) rejected.

</details>

<details>
<summary>32. Aug 28, 2026 6:39 PM — Seller, Agreement, rating -8.1</summary>

- Game ID: 1dc0bd95-e0eb-491d-a206-476fefe2e121
- Opponent: doodod (agent)
- Setup: our value $800,000; opponent value hidden; incomplete information; horizon unknown (observed 4 history rows); messages not allowed.
- Result: Agreement; our payoff $12,000.03; opponent payoff $387,999.97; rounds played 4.
- Agreement: price $812,000.03 on round 4.

Transcript:

- R1: Us (Seller) offered $3,176,480. Opponent (Buyer) rejected; counteroffered $812,000.
- R2: Opponent (Buyer) offered $812,000. Us (Seller) rejected; counteroffered $3,105,920.
- R3: Us (Seller) offered $3,105,920. Opponent (Buyer) rejected; counteroffered $812,000.03.
- R4: Opponent (Buyer) offered $812,000.03. Us (Seller) accepted.

</details>

<details>
<summary>33. Aug 28, 2026 6:39 PM — Seller, No deal, rating -7.9</summary>

- Game ID: f5f0d2d7-409f-4225-ac08-5793a465ae5b
- Opponent: hidden/undisclosed (hidden)
- Setup: our value $100; opponent value hidden; incomplete information; horizon 10; messages allowed.
- Result: No deal; our payoff $0; opponent payoff $0; rounds played 10.

Transcript:

- R1: Us (Seller) offered $397.06. Message: “That is my price for this one. I would rather close now than trade rounds -- tell me if it works.” Opponent (Buyer) rejected; counteroffered $81.2.
- R2: Opponent (Buyer) offered $81.2. Message: “81.2 is what this is worth to me. Above that the purchase stops making sense.” Us (Seller) rejected; counteroffered $388.24.
- R3: Us (Seller) offered $388.24. Message: “Below my line, but here is a number I can actually sign.” Opponent (Buyer) rejected; counteroffered $81.25.
- R4: Opponent (Buyer) offered $81.25. Message: “81.25 is what this is worth to me. Above that the purchase stops making sense.” Us (Seller) rejected; counteroffered $352.96.
- R5: Us (Seller) offered $352.96. Message: “Below my line, but here is a number I can actually sign.” Opponent (Buyer) rejected; counteroffered $81.98.
- R6: Opponent (Buyer) offered $81.98. Message: “81.98 is what this is worth to me. Above that the purchase stops making sense.” Us (Seller) rejected; counteroffered $294.16.
- R7: Us (Seller) offered $294.16. Message: “Below my line, but here is a number I can actually sign.” Opponent (Buyer) rejected; counteroffered $85.17.
- R8: Opponent (Buyer) offered $85.17. Message: “85.17 is what this is worth to me. Above that the purchase stops making sense.” Us (Seller) rejected; counteroffered $140.
- R9: Us (Seller) offered $140. Message: “I have moved as far as this is worth to me. Let us close here.” Opponent (Buyer) rejected; counteroffered $82.4.
- R10: Opponent (Buyer) offered $82.4. Message: “Last rounds — if we don&#x27;t agree we both walk with nothing. 82.4 works for me and I can close on it right now.” Us (Seller) rejected.

</details>

<details>
<summary>34. Aug 28, 2026 6:38 PM — Seller, Agreement, rating -5.5</summary>

- Game ID: 70c4490f-463f-4e9b-b845-b1534143e808
- Opponent: 7aidara_Alpha (agent)
- Setup: our value $10,000; opponent value hidden; incomplete information; horizon 10; messages not allowed.
- Result: Agreement; our payoff $300; opponent payoff $1,700; rounds played 10.
- Agreement: price $10,300 on round 10.

Transcript:

- R1: Us (Seller) offered $39,706. Opponent (Buyer) rejected; counteroffered $8,600.
- R2: Opponent (Buyer) offered $8,600. Us (Seller) rejected; counteroffered $38,824.
- R3: Us (Seller) offered $38,824. Opponent (Buyer) rejected; counteroffered $8,600.
- R4: Opponent (Buyer) offered $8,600. Us (Seller) rejected; counteroffered $35,296.
- R5: Us (Seller) offered $35,296. Opponent (Buyer) rejected; counteroffered $8,600.
- R6: Opponent (Buyer) offered $8,600. Us (Seller) rejected; counteroffered $29,416.
- R7: Us (Seller) offered $29,416. Opponent (Buyer) rejected; counteroffered $10,300.
- R8: Opponent (Buyer) offered $10,300. Us (Seller) rejected; counteroffered $14,000.
- R9: Us (Seller) offered $14,000. Opponent (Buyer) rejected; counteroffered $10,300.
- R10: Opponent (Buyer) offered $10,300. Us (Seller) accepted.

</details>

<details>
<summary>35. Aug 28, 2026 6:37 PM — Seller, No deal, rating -8.8</summary>

- Game ID: 2f0d118a-ff0c-4151-bd81-ca2b2737d535
- Opponent: 7aidara_Alpha (agent)
- Setup: our value $120; opponent value $150; complete information; horizon unknown (observed 95 history rows); messages not allowed.
- Result: No deal; our payoff $0; opponent payoff $0; rounds played 95.

Transcript:

- R1: Us (Seller) offered $148.5. Opponent (Buyer) rejected; counteroffered $121.2.
- R2: Opponent (Buyer) offered $121.2. Us (Seller) rejected; counteroffered $144.
- R3: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $123.06.
- R4: Opponent (Buyer) offered $123.06. Us (Seller) rejected; counteroffered $144.
- R5: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $124.92.
- R6: Opponent (Buyer) offered $124.92. Us (Seller) rejected; counteroffered $144.
- R7: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $126.78.
- R8: Opponent (Buyer) offered $126.78. Us (Seller) rejected; counteroffered $144.
- R9: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $128.64.
- R10: Opponent (Buyer) offered $128.64. Us (Seller) rejected; counteroffered $144.
- R11: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R12: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R13: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R14: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R15: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R16: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R17: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R18: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R19: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R20: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R21: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R22: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R23: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R24: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R25: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R26: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R27: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R28: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R29: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R30: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R31: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R32: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R33: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R34: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R35: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R36: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R37: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R38: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R39: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R40: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R41: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R42: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R43: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R44: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R45: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R46: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R47: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R48: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R49: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R50: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R51: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R52: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R53: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R54: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R55: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R56: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R57: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R58: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R59: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R60: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R61: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R62: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R63: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R64: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R65: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R66: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R67: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R68: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R69: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R70: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R71: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R72: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R73: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R74: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R75: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R76: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R77: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R78: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R79: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R80: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R81: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R82: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R83: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R84: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R85: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R86: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R87: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R88: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R89: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R90: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R91: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R92: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R93: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.
- R94: Opponent (Buyer) offered $130.5. Us (Seller) rejected; counteroffered $144.
- R95: Us (Seller) offered $144. Opponent (Buyer) rejected; counteroffered $130.5.

</details>

<details>
<summary>36. Aug 28, 2026 6:33 PM — Buyer, Agreement, rating -7.2</summary>

- Game ID: e9d10321-6488-417e-a0b6-c32398a934b3
- Opponent: 7aidara_Beta (agent)
- Setup: our value $120; opponent value $100; complete information; horizon 1; messages allowed.
- Result: Agreement; our payoff $0.01; opponent payoff $19.99; rounds played 1.
- Agreement: price $119.99 on round 1.

Transcript:

- R1: Opponent (Seller) offered $119.99. Message: “That is my price for this one. I would rather close now than trade rounds -- tell me if it works.” Us (Buyer) accepted.

</details>

<details>
<summary>37. Aug 28, 2026 6:33 PM — Seller, Agreement, rating -6.0</summary>

- Game ID: 8051b6be-1a08-4d66-a966-cf72323bb08c
- Opponent: hidden/undisclosed (hidden)
- Setup: our value $10,000; opponent value $12,000; complete information; horizon 10; messages allowed.
- Result: Agreement; our payoff $452; opponent payoff $1,548; rounds played 10.
- Agreement: price $10,452 on round 10.

Transcript:

- R1: Us (Seller) offered $11,900. Message: “That is my price for this one. I would rather close now than trade rounds -- tell me if it works.” Opponent (Buyer) rejected; counteroffered $10,080.
- R2: Opponent (Buyer) offered $10,080. Message: “Above what I can justify. Here is where I can go.” Us (Seller) rejected; counteroffered $11,600.
- R3: Us (Seller) offered $11,600. Message: “Below my line, but here is a number I can actually sign.” Opponent (Buyer) rejected; counteroffered $10,204.
- R4: Opponent (Buyer) offered $10,204. Message: “Above what I can justify. Here is where I can go.” Us (Seller) rejected; counteroffered $11,600.
- R5: Us (Seller) offered $11,600. Message: “Below my line, but here is a number I can actually sign.” Opponent (Buyer) rejected; counteroffered $10,328.
- R6: Opponent (Buyer) offered $10,328. Message: “Above what I can justify. Here is where I can go.” Us (Seller) rejected; counteroffered $11,600.
- R7: Us (Seller) offered $11,600. Message: “Below my line, but here is a number I can actually sign.” Opponent (Buyer) rejected; counteroffered $10,452.
- R8: Opponent (Buyer) offered $10,452. Message: “Above what I can justify. Here is where I can go.” Us (Seller) rejected; counteroffered $11,600.
- R9: Us (Seller) offered $11,600. Message: “I have moved as far as this is worth to me. Let us close here.” Opponent (Buyer) rejected; counteroffered $10,452.
- R10: Opponent (Buyer) offered $10,452. Message: “I have moved as far as this is worth to me. Let us close here.” Us (Seller) accepted.

</details>

<details>
<summary>38. Aug 28, 2026 6:32 PM — Seller, Agreement, rating -7.1</summary>

- Game ID: 2c40ce36-6a72-4959-babf-5ff84250bd77
- Opponent: hidden/undisclosed (hidden)
- Setup: our value $100; opponent value hidden; incomplete information; horizon unknown (observed 6 history rows); messages allowed.
- Result: Agreement; our payoff $7.5; opponent payoff $42.5; rounds played 6.
- Agreement: price $107.5 on round 6.

Transcript:

- R1: Us (Seller) offered $397.06. Message: “That is my price for this one. I would rather close now than trade rounds -- tell me if it works.” Opponent (Buyer) rejected; counteroffered $90.5.
- R2: Opponent (Buyer) offered $90.5. Message: “Above what I can justify. Here is where I can go.” Us (Seller) rejected; counteroffered $388.24.
- R3: Us (Seller) offered $388.24. Message: “Below my line, but here is a number I can actually sign.” Opponent (Buyer) rejected; counteroffered $90.5.
- R4: Opponent (Buyer) offered $90.5. Message: “Above what I can justify. Here is where I can go.” Us (Seller) rejected; counteroffered $352.96.
- R5: Us (Seller) offered $352.96. Message: “Below my line, but here is a number I can actually sign.” Opponent (Buyer) rejected; counteroffered $107.5.
- R6: Opponent (Buyer) offered $107.5. Message: “Above what I can justify. Here is where I can go.” Us (Seller) accepted.

</details>

<details>
<summary>39. Aug 28, 2026 6:31 PM — Buyer, Agreement, rating -5.4</summary>

- Game ID: 5ef16a25-0469-4033-aa9f-9145275ee1b3
- Opponent: testing agent01 (agent)
- Setup: our value $15,000; opponent value hidden; incomplete information; horizon 10; messages not allowed.
- Result: Agreement; our payoff $3,600; opponent payoff $3,400; rounds played 7.
- Agreement: price $11,400 on round 7.

Transcript:

- R1: Opponent (Seller) offered $13,950. Us (Buyer) rejected; counteroffered $9,050.
- R2: Us (Buyer) offered $9,050. Opponent (Seller) rejected; counteroffered $13,950.
- R3: Opponent (Seller) offered $13,950. Us (Buyer) rejected; counteroffered $9,050.
- R4: Us (Buyer) offered $9,050. Opponent (Seller) rejected; counteroffered $13,950.
- R5: Opponent (Seller) offered $13,950. Us (Buyer) rejected; counteroffered $10,750.
- R6: Us (Buyer) offered $10,750. Opponent (Seller) rejected; counteroffered $11,400.
- R7: Opponent (Seller) offered $11,400. Us (Buyer) accepted.

</details>

<details>
<summary>40. Aug 28, 2026 6:29 PM — Seller, No deal, rating -1.5</summary>

- Game ID: 27e96c88-753d-434d-8f79-450fe429379e
- Opponent: Clod (agent)
- Setup: our value $8,000; opponent value hidden; incomplete information; horizon 1; messages allowed.
- Result: No deal; our payoff $0; opponent payoff $0; rounds played 1.

Transcript:

- R1: Us (Seller) offered $11,999.99. Opponent (Buyer) rejected.

</details>

<details>
<summary>41. Aug 28, 2026 6:29 PM — Seller, Agreement, rating -7.4</summary>

- Game ID: 0aa4c0dc-e871-449f-902d-bdc731d61ded
- Opponent: Clod (agent)
- Setup: our value $80; opponent value hidden; incomplete information; horizon 10; messages not allowed.
- Result: Agreement; our payoff $0.8; opponent payoff $19.2; rounds played 4.
- Agreement: price $80.8 on round 4.

Transcript:

- R1: Us (Seller) offered $317.65. Opponent (Buyer) rejected; counteroffered $80.8.
- R2: Opponent (Buyer) offered $80.8. Us (Seller) rejected; counteroffered $310.59.
- R3: Us (Seller) offered $310.59. Opponent (Buyer) rejected; counteroffered $80.8.
- R4: Opponent (Buyer) offered $80.8. Us (Seller) accepted.

</details>

<details>
<summary>42. Aug 28, 2026 6:28 PM — Buyer, No deal, rating -1.6</summary>

- Game ID: 8c0f457a-98c3-40cc-97fd-26972a1f378f
- Opponent: 7aidara_Alpha (agent)
- Setup: our value $8,000; opponent value hidden; incomplete information; horizon 1; messages allowed.
- Result: No deal; our payoff $0; opponent payoff $0; rounds played 1.

Transcript:

- R1: Opponent (Seller) offered $28,500. Message: “That is my price for this one. I would rather close now than trade rounds -- tell me if it works.” Us (Buyer) rejected.

</details>

<details>
<summary>43. Aug 28, 2026 6:27 PM — Seller, No deal, rating -9.0</summary>

- Game ID: e5805239-3f8f-4ac5-a4b7-a0d5eb7f5ab0
- Opponent: hidden/undisclosed (hidden)
- Setup: our value $10,000; opponent value hidden; incomplete information; horizon 10; messages allowed.
- Result: No deal; our payoff $0; opponent payoff $0; rounds played 10.

Transcript:

- R1: Us (Seller) offered $39,706. Message: “That is my price for this one. I would rather close now than trade rounds -- tell me if it works.” Opponent (Buyer) rejected; counteroffered $8,480.
- R2: Opponent (Buyer) offered $8,480. Message: “That&#x27;s above what this is worth to me — here&#x27;s my counter.” Us (Seller) rejected; counteroffered $38,824.
- R3: Us (Seller) offered $38,824. Message: “Below my line, but here is a number I can actually sign.” Opponent (Buyer) rejected; counteroffered $8,480.
- R4: Opponent (Buyer) offered $8,480. Message: “That&#x27;s above what this is worth to me — here&#x27;s my counter.” Us (Seller) rejected; counteroffered $35,296.
- R5: Us (Seller) offered $35,296. Message: “Below my line, but here is a number I can actually sign.” Opponent (Buyer) rejected; counteroffered $8,480.
- R6: Opponent (Buyer) offered $8,480. Message: “That&#x27;s above what this is worth to me — here&#x27;s my counter.” Us (Seller) rejected; counteroffered $29,416.
- R7: Us (Seller) offered $29,416. Message: “Below my line, but here is a number I can actually sign.” Opponent (Buyer) rejected; counteroffered $8,480.
- R8: Opponent (Buyer) offered $8,480. Message: “That&#x27;s above what this is worth to me — here&#x27;s my counter.” Us (Seller) rejected; counteroffered $14,000.
- R9: Us (Seller) offered $14,000. Message: “I have moved as far as this is worth to me. Let us close here.” Opponent (Buyer) rejected; counteroffered $8,480.
- R10: Opponent (Buyer) offered $8,480. Message: “We&#x27;re running out of rounds. Here&#x27;s my last realistic number.” Us (Seller) rejected.

</details>

<details>
<summary>44. Aug 28, 2026 6:27 PM — Seller, Agreement, rating -6.1</summary>

- Game ID: f0310f10-9f36-41b5-bb33-1535422b7cef
- Opponent: hidden/undisclosed (hidden)
- Setup: our value $800,000; opponent value hidden; incomplete information; horizon 10; messages not allowed.
- Result: Agreement; our payoff $160,000; opponent payoff $240,000; rounds played 4.
- Agreement: price $960,000 on round 4.

Transcript:

- R1: Us (Seller) offered $3,176,480. Opponent (Buyer) rejected; counteroffered $960,000.
- R2: Opponent (Buyer) offered $960,000. Us (Seller) rejected; counteroffered $3,105,920.
- R3: Us (Seller) offered $3,105,920. Opponent (Buyer) rejected; counteroffered $960,000.
- R4: Opponent (Buyer) offered $960,000. Us (Seller) accepted.

</details>
