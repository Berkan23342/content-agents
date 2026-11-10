# Outbreak Diary: Harbor View, story bible

The one place that remembers the story. The writer reads it before every episode and updates **Current state** and
**Episode log** after writing one. Everything here is original and fictional.

## The world

- **Port Ellis**, a rainy harbour city. It is fictional; never name real cities, brands or people.
- **Harbor View**, an old 12-storey apartment block three streets from the water. The narrator lives in **9C**.
  - The elevator still works while there is power.
  - The stairwell is dark and loud.
  - The roof door needs the super's key.
- **Pier Four**, two miles away at the harbour. The radio says boats take people off the coast.

## The infected ("them")

The narrator calls them "them" or "the infected", never "zombies". Titles may say "zombie".

- They hunt by **sound**, not sight. Silence keeps you alive. A barking dog is dangerous.
- They are slow and clumsy on **stairs** and cannot work door handles. Upper floors are safer.
- They are sluggish by day and restless at night.
- A bite brings a fever within hours. Then the person goes quiet, then they change.
- Rain hides sound. Survivors move in the rain.

## People

- **Sam (the narrator)**, late twenties, a bike courier who knows every shortcut in Port Ellis. Speaks in short, honest
  sentences, a little dry humour, scared but stubborn. Lives alone with:
- **Biscuit**, a small scruffy terrier mix. Brave, nosy, hates thunder. Biscuit must never die.
- **Mrs. Okafor (7B)**, seventy-two, a retired nurse. Calm, sharp and bossy. She keeps tomatoes on her balcony and
  owns an old battery radio.
- **Leo (11C)**, fourteen. His parents went out to find his sister on Day 1 and have not come back. He hides it with jokes.
- **Mr. Hale (3A)**, the building super. He has the keys to the roof and to the basement generator. Status unknown.

## Season plan (ends on Day 15)

The story ends on Day 15 (story/series.json `finale`); after that its slot goes to a new story. Days 1-13 are told
(see the Episode log). Land it:

- **Day 14.** Pier Four at night: free Biscuit from Marek and the pier's dead. Hale's generator key is the way out.
- **Day 15, the finale.** The tug leaves the harbour with Sam, Biscuit, Mrs. Okafor, Leo, Dara and Hale. Answer the
  big questions (Biscuit is safe, the boat really leaves) and end on one quiet, strong image: Harbor View's lit window
  shrinking in the rain, or a light answering from across the water. No cliffhanger that needs a Day 16.

## Voices

- The narrator is always the woman telling the story.
- A character can say a line in their own voice: put the spoken words alone in a beat with `"speaker"`. For example,
  `{"text": "Stay away from the door.", "speaker": "..."}`. The narration around it says who speaks ("Then a voice
  whispered.").
- Speakers in this story: `okafor` (Mrs. Okafor), `leo`, `hale` (Mr. Hale), `announcer` (the Harbor Station radio voice). Anyone else is quoted by the narrator.
- Use one or two spoken lines per part. They make the story feel alive.

## Rules for every part

- **One part is one day.** Part N is Day N: the video shows "DAY N" by itself, and a first line that names the day says
  "Day N." Never give two parts the same day.
- 45-65 seconds: 100-125 words, 8-14 beats.
- The first line is a hook. The last line is a cliffhanger.
- First person, past tense, short sentences.
- PG-13: tension and danger, never gore, no swearing, no cruelty to animals.
- Every part moves the story forward a little: one new problem, one discovery, or one decision.

## Places

- Scenes to use: Sam's apartment and building (`room`, `door`, `peephole`, `hallway`, `stairwell`, `kitchen`,
  `window`, `building`, `rooftop`), plus `lobby` (Harbor View's lobby), `school`, `supermarket`, `hospital` and `subway` (trips outside). Go somewhere new every few parts.

## Current state

- **After:** part 13
- **Day:** 13, dusk, Pier Four (Sam, Leo, Dara, Mrs. Okafor, Hale on the way; Marek and Biscuit on the tug)
- **Who:** all unhurt; Marek holds Biscuit.
- **Supplies:** one can, a rattling tin.
- **Known:** the roof key does not start the tug; Hale holds the real generator key. Marek has just shouted Sam's name and woken the pier.
- **Open threads:** will Marek and Biscuit get free of the pier? Who is on the pier?

## Episode log

- **Part 1 (Day 1) The Sirens:** the sirens and the alert. The street fills. Someone knocks and whispers Sam's name.
- **Part 2 (Day 2) Apartment 7B:** it was Mrs. Okafor, who came up in the elevator. The stairs are full. The
  supplies are small. Biscuit growls at something behind the door.
- **Part 3 (Day 3) Pier Four:** the power goes and the phone loses signal. The radio says boats leave Pier Four in
  three days, two miles and nine floors away.
- **Part 4 (Day 4) Three Taps:** at night the pipes tap in code. Sam answers; three taps reply from above and one from
  below.
- **Part 5 (Day 5) The Boy in 11C:** Sam finds Leo in 11C. His walkie-talkie picks up Mr. Hale, who has the roof key and
  warns that they are inside the stairwell.
- **Part 6 (Day 6) The Last Horn:** the boat's horn sounds at dawn and they miss it. The radio promises a last boat in
  three days. Hale says he tapped once and offers the roof, but a door below him just opened. Biscuit growls at the door.
- **Part 7 (Day 7) The Fourth Floor:** Hale asks them to come down the back stairs at noon. Sam and Leo descend; the shapes below turn toward them and Biscuit opens his mouth.
- **Part 8 (Day 8) Hale's Key:** Biscuit yawns silently and the shapes drift off. Hale gives Sam the roof key; they plan to climb to 12 in the rain. Mrs. Okafor reports three slow knocks at her door.
- **Part 9 (Day 9) The Roof Door:** the three knocks were Leo's sister Dara. They climb to 12 and find the roof door already open and a stranger who says the last boat has gone.
- **Part 10 (Day 10) The Pilot:** Marek offers a tug at Pier Four if they fetch diesel from the basement. Hale warns over the walkie that the pilot is not alone.
- **Part 11 (Day 11) The Generator Room:** Marek's three-person crew waits in the basement; Hale is locked in the generator room. Mrs. Okafor's clang drives the crew off, Hale is freed, then boots stop outside Sam's hiding place and Marek whispers "Found you."
- **Part 12 (Day 12) Fair Trade:** Marek has Biscuit and trades him for the roof key, taking the dog as insurance. Hale reveals the real tug key is the generator key in his fist.
- **Part 13 (Day 13) The Rail Bridge:** Sam's group crosses the city by supermarket and dead train after Marek. At Pier Four the roof key fails, and Marek shouts Sam's name, waking the pier.
