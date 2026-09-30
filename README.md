# Capture the Flag Admin

`SA-ctf_scoreboard_admin` is the administrator application for the Splunk Capture the Flag stack.

This compatibility repository targets Splunk Enterprise 10.4 and supports multiple concurrent CTFs by using a stable `ctf_id` across registration, questions, answers, hints, submissions, scoring, and administrative views.

## Requirements

- Splunk Enterprise 10.4
- `SA-ctf_scoreboard`
- `SA-ctf_registration`
- Python 3 supplied by Splunk 10.4
- `scoreboard`, `scoreboard_admin`, and `scoreboard_admin_kv` indexes
- Roles:
  - `ctf_admin`
  - `ctf_competitor`
  - `ctf_answers_service`
  - `ctf_registration_admin` when registration administration is delegated

The registration app must be installed because the admin dashboards use its `ctf_events` and `ctf_registrations` data to select and scope events.

## Multi-CTF identity

Use the same `ctf_id` everywhere.

Example:

```text
asteron-easy-2026
```

The following identities are used:

```text
Question:     ctf_id + Number
Answer:       ctf_id + Number
Hint:         ctf_id + Number + HintNumber
Registration: ctf_id + Username
```

Never reuse a `ctf_id` for a different CTF.

## Admin event selector

Multi-CTF administrative dashboards include a CTF selector at the top of the page.

The selector is populated from:

```text
SA-ctf_registration / ctf_events
```

The selected event is exposed to searches as:

```text
$ctf_id$
$ctf_event_name$
```

You can open a dashboard directly for a specific event:

```text
/en-US/app/SA-ctf_scoreboard_admin/q__a?ctf_id=asteron-easy-2026
```

## Creating a CTF

Create the event in:

```text
Capture the Flag Registration
→ CTF Registration Admin
```

Configure:

1. CTF ID
2. name
3. short/full descriptions
4. event image
5. registration open time
6. registration close time
7. event start time
8. event end time
9. search URL
10. scoring URL if used
11. participant roles
12. Enabled
13. Allow registration updates

Record the exact `ctf_id`.

## Loading questions, answers, and hints

Every staged CSV must contain `ctf_id`.

### Questions

```csv
ctf_id,Number,Question,StartTime,EndTime,BasePoints,AdditionalBonusPoints,AdditionalBonusInstructions
asteron-easy-2026,1,"What host was initially compromised?",1791806400,1791982800,100,0,""
```

### Answers

```csv
ctf_id,Number,Answer
asteron-easy-2026,1,WEB-01
```

### Hints

```csv
ctf_id,Number,HintNumber,Hint,HintCost
asteron-easy-2026,1,1,"Review authentication events.",10
```

The multi-CTF staged loaders merge by event/question identity instead of replacing unrelated CTF content:

```text
questions: ctf_id + Number
answers:   ctf_id + Number
hints:     ctf_id + Number + HintNumber
```

## Time bounding

There are two layers of time control.

### Event-level time control

Managed by `SA-ctf_registration`:

```text
registration_opens
registration_closes
event_starts
event_ends
```

### Question-level scoring time control

Stored in `ctf_questions`:

```text
StartTime
EndTime
```

Use **Time Setup** in the admin app to update question times for only the currently selected CTF. Other CTF rows are preserved.

Recommended relationship:

```text
event_starts <= question StartTime <= question EndTime <= event_ends
```

## Enabling registration

Registration accepts a participant only when:

- the event exists
- the event is enabled
- current server time is inside its registration window
- requested participant roles are permitted

The normal participant role is:

```text
ctf_competitor
```

## Validating content before an event

Questions:

```spl
| inputlookup ctf_questions
| search ctf_id="asteron-easy-2026"
| stats count
```

Answers:

```spl
| inputlookup ctf_answers
| search ctf_id="asteron-easy-2026"
| stats count
```

Hints:

```spl
| inputlookup ctf_hints
| search ctf_id="asteron-easy-2026"
| stats count
```

Find questions missing answers:

```spl
| inputlookup ctf_questions
| search ctf_id="asteron-easy-2026"
| lookup ctf_answers ctf_id Number OUTPUT Answer
| where isnull(Answer)
| table ctf_id Number Question
```

Registered competitors:

```spl
| inputlookup ctf_registrations
| search ctf_id="asteron-easy-2026" status="registered"
| table Username DisplayUsername Team
```

## Starting a CTF

Before start:

1. create and enable the event in the registration app
2. verify registration timing
3. load questions, answers, and hints with the same `ctf_id`
4. verify question StartTime/EndTime
5. register a test competitor
6. open Q & A in this admin app and select the event
7. submit one test answer
8. verify the score event contains `ctf_id`

Example:

```spl
index=scoreboard ctf_id="asteron-easy-2026"
| head 20
| table _time ctf_id Team user Number Result BasePointsAwarded Penalty
```

## Concurrent CTFs

Different CTFs may use the same question numbers.

These are distinct:

```text
asteron-easy-2026 / Question 1
asteron-hard-2026 / Question 1
```

Admin views filter using the selected `ctf_id`.

The generated `currentscore.csv` also contains `ctf_id`, and rank is calculated separately per CTF.

## Adjusting scores

Open **Adjust Scores**, select the CTF at the top, then select registered users/teams and a question.

The adjustment request includes:

```text
ctf_id
```

so adjustments cannot collide with the same question number in another CTF.

## Closing registration

Registration closes automatically at `registration_closes`.

To close it immediately:

- set the registration close time to now/past, or
- disable the event if it should no longer be available

## Closing out a CTF

After the event:

1. verify `event_ends`
2. verify registration is closed
3. verify final scoring for the event
4. export/archive results if required
5. retain the original `ctf_id`
6. disable the event when it should no longer be presented
7. do not delete or reuse historical event IDs merely to clean up the UI

Final score check:

```spl
index=scoreboard ctf_id="asteron-easy-2026"
| stats max(BasePointsAwarded) as BasePoints
        max(SpeedBonusAwarded) as SpeedBonus
        max(AdditionalBonusAwarded) as AdditionalBonus
        sum(Penalty) as Penalty
  by Team Number
| eval QuestionScore=BasePoints+SpeedBonus+AdditionalBonus-Penalty
| stats sum(QuestionScore) as Score by Team
| sort - Score
```

## Splunk 10.4 compatibility

Custom commands that require the caller session key must retain:

```ini
passauth = true
```

for `checkqaccess` and `toggleqaccess`.

Do not restore the upstream Python 2 implementations over the compatibility versions in `overrides/bin`.

## Logs

```text
$SPLUNK_HOME/var/log/scoreboard/scoreboard_admin.log
```

Rootless Podman:

```bash
podman exec -u splunk splunk \
  tail -f /opt/splunk/var/log/scoreboard/scoreboard_admin.log
```

## Build

This repository is an overlay build. Files under `overrides/` are copied over the pinned upstream app during the build.

Run:

```bash
make build
```

or the repository's documented build target.

## Related apps

- `SA-ctf_registration` — event definitions, registration windows, event windows, participant registration, role assignment
- `SA-ctf_scoreboard` — participant questions, submissions, hints, and scoring

## Content ownership and upgrades

`SA-ctf_scoreboard_admin` is the authoritative owner of the three event-content KV Store collections:

```text
ctf_questions
ctf_answers
ctf_hints
```

`ctf_questions` is exported system-wide so `SA-ctf_scoreboard` can display questions, but the collection itself remains in the admin app namespace. Answers and hints remain protected in the admin app.

The compatibility build explicitly carries the collection and transform definitions for all three collections. Updating the app in place does not intentionally delete existing KV Store rows; however, a package that omits a collection definition can make existing data unavailable through `inputlookup`. The build tests therefore verify that `ctf_questions` is present in the final overlay. Back up KV Store content before uninstalling/replacing the app entirely.

The existing `backup-scoreboard.py` utility discovers all collections in both scoreboard apps, so once `ctf_questions` is owned here it is included in normal admin-app KV Store backups.
