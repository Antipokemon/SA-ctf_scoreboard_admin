# Capture the Flag Admin

`SA-ctf_scoreboard_admin` is the administrative companion to `SA-ctf_scoreboard`.

This repository modernizes the original CTF administrator app for Splunk Enterprise 10.4. It manages protected CTF content and administrative scoring functions.

The multi-CTF architecture uses `ctf_id` to keep answers, hints, questions, registrations, and scores separated when more than one CTF exists at the same time.

## Requirements

- Splunk Enterprise 10.4
- `SA-ctf_scoreboard`
- `SA-ctf_registration`
- Splunk administrator or a user assigned the CTF administrative role
- Roles:
  - `ctf_admin`
  - `ctf_competitor`
  - `ctf_answers_service`
  - `ctf_registration_admin` where registration administration is delegated
- The `scoreboard` and `scoreboard_admin` indexes
- Python 3 as provided by Splunk 10.4
- CTF content consistently tagged with the same `ctf_id`

App ID:

```text
SA-ctf_scoreboard_admin
```

Display name:

```text
Capture the Flag Admin
```

## Responsibilities by app

### `SA-ctf_registration`

Owns:

- CTF definitions
- event images/descriptions
- registration open/close times
- event start/end times
- participant registration
- participant role assignment

### `SA-ctf_scoreboard`

Owns:

- participant question display
- answer submission
- hint purchases
- participant scoring events
- participant-facing score views

### `SA-ctf_scoreboard_admin`

Owns/protects:

- official answers
- official hints
- administrative score adjustments
- administrative content and scoring workflows

## Multi-CTF requirement

Every event must have a stable:

```text
ctf_id
```

Example:

```text
asteron-easy-2026
```

The same `ctf_id` must be used in:

```text
SA-ctf_registration / ctf_events
SA-ctf_registration / ctf_registrations
SA-ctf_scoreboard / ctf_questions
SA-ctf_scoreboard_admin / ctf_answers
SA-ctf_scoreboard_admin / ctf_hints
scoreboard events
scoreboard_admin events
```

Never use two different spellings for the same event.

## Creating a CTF

The event itself is created in **Capture the Flag Registration**, not in the admin scoreboard.

Open:

```text
/en-US/app/SA-ctf_registration/admin
```

Create the CTF and record its exact `ctf_id`.

Example:

```text
asteron-easy-2026
```

Configure:

```text
Name
Short description
Full description
Image
Registration opens
Registration closes
Event starts
Event ends
Search URL
Scoring URL
Participant roles
Enabled
Allow updates
```

After the event exists, load the questions, answers, and hints for the same `ctf_id`.

## Content-loading order

Recommended order:

1. create the CTF in `SA-ctf_registration`
2. load questions into `SA-ctf_scoreboard`
3. load answers into `SA-ctf_scoreboard_admin`
4. load hints into `SA-ctf_scoreboard_admin`
5. verify question/answer/hint counts
6. test registration
7. test one participant answer
8. test one hint purchase
9. open registration to users

## Answers

Official answers are protected in:

```text
ctf_answers
```

For multi-CTF operation, answer identity is:

```text
ctf_id + Number
```

Example:

```csv
ctf_id,Number,Answer
asteron-easy-2026,1,WEB-01
asteron-easy-2026,2,10.20.30.40
```

Question `1` from another CTF is allowed:

```csv
asteron-hard-2026,1,VPN-EDGE-02
```

because the `ctf_id` differs.

## Hints

Hints are protected in:

```text
ctf_hints
```

Hint identity is:

```text
ctf_id + Number + HintNumber
```

Example:

```csv
ctf_id,Number,HintNumber,Hint,HintCost
asteron-easy-2026,1,1,"Look at authentication events.",10
asteron-easy-2026,1,2,"Focus on WEB-01.",20
```

## Questions

Questions are stored by `SA-ctf_scoreboard` in:

```text
ctf_questions
```

Expected event-scoped fields:

```text
ctf_id
Number
Question
StartTime
EndTime
BasePoints
AdditionalBonusPoints
AdditionalBonusInstructions
```

The administrator app and participant app must use the same `ctf_id + Number`.

## Validating a CTF before opening registration

### Questions

```spl
| inputlookup ctf_questions
| search ctf_id="asteron-easy-2026"
| stats count as questions
```

### Answers

```spl
| inputlookup ctf_answers
| search ctf_id="asteron-easy-2026"
| stats count as answers
```

### Hints

```spl
| inputlookup ctf_hints
| search ctf_id="asteron-easy-2026"
| stats count as hints
```

### Find questions without answers

```spl
| inputlookup ctf_questions
| search ctf_id="asteron-easy-2026"
| fields ctf_id Number Question
| lookup ctf_answers ctf_id Number OUTPUT Answer
| where isnull(Answer)
```

Do not open the event until required questions have matching official answers.

## Time-bounding an event

Event-level dates are configured in `SA-ctf_registration`.

The four event-level timestamps are:

```text
registration_opens
registration_closes
event_starts
event_ends
```

Question-level scoring dates remain in:

```text
ctf_questions.StartTime
ctf_questions.EndTime
```

Recommended relationship:

```text
event_starts
    <= question StartTime
    <= question EndTime
    <= event_ends
```

This is a convention for event consistency; use intentional exceptions only when the scenario requires them.

## Enabling registration

Registration is controlled from:

```text
Capture the Flag Registration → CTF Registration Admin
```

For a CTF to accept registration:

1. the event must exist
2. `enabled` must be true
3. current time must be inside the event's registration window
4. the participant role must be allowed by the registration app

The normal participant role is:

```text
ctf_competitor
```

The registration backend adds that role to the Splunk user without removing the user's existing roles.

## Opening an event

Before the event starts:

1. confirm registration state is correct
2. confirm event start/end times
3. confirm questions use the event's `ctf_id`
4. confirm answers use the event's `ctf_id`
5. confirm hints use the event's `ctf_id`
6. confirm participant registration exists
7. verify a participant sees only the selected event
8. submit one test answer
9. verify resulting events contain `ctf_id`

Example:

```spl
index=scoreboard ctf_id="asteron-easy-2026"
| head 20
| table _time ctf_id Team user Number Result BasePointsAwarded Penalty
```

## Concurrent CTFs

Multiple CTFs can use the same question numbers.

Example:

```text
asteron-easy-2026 / Question 1
asteron-hard-2026 / Question 1
```

This works only if questions, answers, hints, hint entitlements, and score events are all scoped with `ctf_id`.

Do not rely on `Number` alone.

## Closing registration

Registration normally closes automatically when:

```text
registration_closes
```

passes.

To close it immediately, edit the CTF in the registration admin page and either:

- set the registration close time to now/past, or
- disable the event if the event should no longer be available at all

## Closing out a CTF

At event completion:

1. allow or set `event_ends`
2. verify registration is closed
3. stop any event-specific operational activity
4. preserve the `ctf_id`
5. export/archive scores if required
6. retain official answers and hints as needed for historical review
7. disable the registration event when it should no longer be shown
8. do not reuse the `ctf_id`

Suggested final score validation:

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

## Service account

`SA-ctf_scoreboard` uses a privileged service account to retrieve protected answers.

That account should use the dedicated role:

```text
ctf_answers_service
```

Do not give normal competitors direct read access to `ctf_answers`.

The service account credentials are stored in the participant app's local controller configuration and must not be committed to Git.

## Splunk 10.4 compatibility

The modernized administrator app uses Python 3-compatible custom commands.

Commands that need the caller's Splunk session key must use:

```ini
passauth = true
```

For example:

```ini
[checkqaccess]
filename = checkqaccess.py
chunked = false
generating = true
enableheader = true
passauth = true
python.required = 3.9,3.13
```

and similarly for `toggleqaccess`.

## Administrative role

Verify:

```text
ctf_admin
```

is present and assigned to CTF administrators.

Example:

```bash
podman exec -u splunk splunk \
  /opt/splunk/bin/splunk btool authorize list ctf_admin --debug
```

## Logs

Administrative scoreboard log:

```text
$SPLUNK_HOME/var/log/scoreboard/scoreboard_admin.log
```

Example:

```bash
podman exec -u splunk splunk \
  tail -f /opt/splunk/var/log/scoreboard/scoreboard_admin.log
```

## Troubleshooting

### `checkqaccess` says no session key was provided

Verify `passauth = true` in:

```text
default/commands.conf
```

for both:

```text
checkqaccess
toggleqaccess
```

### Answer lookup crosses CTFs

Verify `ctf_answers` contains `ctf_id` and that the participant controller is filtering by both:

```text
ctf_id
Number
```

### Hint lookup crosses CTFs

Verify `ctf_hints` is scoped by:

```text
ctf_id
Number
HintNumber
```

### Old dashboard JavaScript appears after deployment

Restart Splunk and validate in a private browser window to eliminate stale browser/static cache while testing.

## Recommended event lifecycle

```text
Create CTF
    ↓
Load Questions / Answers / Hints
    ↓
Validate content by ctf_id
    ↓
Enable event
    ↓
Registration window opens
    ↓
Participants register
    ↓
Event starts
    ↓
Event runs
    ↓
Registration closes (at configured time)
    ↓
Event ends
    ↓
Validate/export results
    ↓
Disable/archive event
```

## Related apps

- `SA-ctf_registration` — event definitions, time windows, registration, and participant role assignment
- `SA-ctf_scoreboard` — participant questions, answers, hints, and scoring
