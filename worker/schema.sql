-- Anonymous guess logging for The Narrated Self (docs/PREREGISTRATION.md §9).
-- No IP address, user agent, cookie or account is stored.

CREATE TABLE IF NOT EXISTS guesses (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  received_at  TEXT    NOT NULL,           -- server time, UTC ISO 8601
  round        TEXT    NOT NULL,           -- e.g. R0
  mode         TEXT    NOT NULL,           -- quiz | control
  device_id    TEXT    NOT NULL,           -- random ID kept in the player's browser
  set_id       TEXT    NOT NULL,           -- random ID per set (quiz) or per pair (control)
  first_set    INTEGER NOT NULL,           -- 1 if this device had not finished a set before
  story_id     TEXT    NOT NULL,           -- quiz: the story shown; control: the story picked as the robot arm
  other_id     TEXT,                       -- control only: the other story in the pair
  true_model   TEXT    NOT NULL,           -- looked up server-side from the published round data
  theme        TEXT    NOT NULL,
  cond         TEXT    NOT NULL,
  guess        TEXT    NOT NULL,           -- quiz: model guessed; control: "robot"
  correct      INTEGER NOT NULL,           -- computed server-side
  position     INTEGER NOT NULL,           -- 1-based position in the set
  ms_to_guess  INTEGER NOT NULL,           -- from story shown to guess
  is_bot       INTEGER NOT NULL            -- known bot user agent (the user agent itself is not stored)
);
CREATE INDEX IF NOT EXISTS idx_guesses_round ON guesses (round, mode);
CREATE INDEX IF NOT EXISTS idx_guesses_device ON guesses (device_id, received_at);

CREATE TABLE IF NOT EXISTS profiles (
  device_id    TEXT PRIMARY KEY,
  uses_most    TEXT NOT NULL,              -- answer to the optional "Which AI assistant do you use most?"
  received_at  TEXT NOT NULL
);
