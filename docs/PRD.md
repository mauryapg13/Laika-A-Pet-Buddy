# PawHub — Product Requirements Document

**Status:** Draft for engineering and ML handoff  
**Version:** 0.1  
**Date:** 2026-09-27  
**Product:** Modular tactile interaction hub for dogs  
**Audience:** Product, industrial design, mechanical engineering, embedded systems, mobile, backend, ML, QA, animal-behavior advisors

---

## 1. Executive summary

PawHub is a wall-mounted interaction hub designed to give dogs a physical, consistent way to communicate, play, and participate in household routines.

Voice is the primary interaction method for human smart speakers. PawHub instead uses:

- Touch and nose presses.
- Pulling and releasing.
- Texture and shape.
- Controlled resistance.
- Light, sound, and gentle ear movements.
- Physical outputs such as treat drops, ball rolls, or harness release.

The product is not intended to translate a dog's thoughts or diagnose emotion. It provides a vocabulary of repeatable physical actions whose meanings are defined by the owner during onboarding.

The v1 product has:

- One large central boop pad.
- Five modular perimeter nodes.
- Two expressive ears.
- Camera, microphone, speaker, lights, and local sensors.
- A mobile app for configuration, schedules, review, and notifications.
- A deterministic interaction engine.
- ML-assisted recognition, personalization, anomaly detection, and daily summaries.

The central behavioral decision is:

> “Unavailable” must not mean “pull harder.”

When a pull interaction is unavailable, its handle is physically parked or retracted and its invitation cues are absent. The system must never teach a dog that increasing force overcomes “no.” Adaptive resistance is used only inside a clearly announced play or workout session.

---

## 2. Product vision

Create a shared physical language between dogs and humans that is:

- Understandable through repetition.
- Consistent across time.
- Tactile rather than screen-dependent.
- Useful while the owner is home or away.
- Delightful without being overstimulating.
- Safe under excited, repetitive, and imperfect use.

The hub should feel like a calm household companion, not gym machinery, a vending machine, or a surveillance device.

---

## 3. Users

### Primary purchaser

- Upper-middle-income or affluent dog owner.
- Works outside the home or has long meetings.
- Wants more interaction, enrichment, and insight into the dog's day.
- Comfortable using a mobile app to configure routines.

### Primary physical user

- A healthy adult dog capable of approaching and interacting with the wall-mounted hub.
- Initial target testing should focus on medium and large companion dogs.

### Secondary users

- Other household members.
- Dog walkers and pet sitters.
- Trainers, veterinary behaviorists, and support staff.

### Initial exclusions

The product should not be positioned for unsupervised resistance play with:

- Dogs with known resource guarding around toys or food.
- Dogs with a history of destructive pulling or fixation.
- Dogs recovering from neck, jaw, spinal, or limb injuries.
- Puppies or dogs unable to follow a trained release cue.

These cases require separate testing and professional guidance.

---

## 4. Goals

### Product goals

1. Give dogs a small, consistent tactile vocabulary.
2. Make availability and unavailability physically obvious.
3. Support both communication and enrichment without confusing them.
4. Provide owners with useful, factual summaries of the dog's day.
5. Allow new attachments without redesigning the complete hub.
6. Make the hub feel appropriate in a premium home.

### Behavioral goals

1. Reinforce one clear action rather than repeated escalating actions.
2. Allow the dog to opt in, pause, or leave.
3. End sessions calmly and predictably.
4. Avoid rewarding harder pulling, repeated barking, or frantic repetition.
5. Give owners control over schedules, availability, and reward limits.

### Engineering goals

1. Safety rules must work without the ML model.
2. Maximum force, speed, travel, temperature, and session duration must have hard limits.
3. Attachments must be identified automatically.
4. Food-contact components must be removable from electronics for cleaning.
5. Logged events must be sufficient for model training and debugging.

---

## 5. Non-goals

PawHub v1 will not:

- Claim to read a dog's mind or accurately infer hunger from pulling force.
- Diagnose anxiety, aggression, pain, illness, or other medical conditions.
- Use stronger resistance as punishment.
- Allow ML to override mechanical safety limits.
- Automatically begin high-arousal resistance play solely from camera predictions.
- Reward barking by default.
- Dispense unlimited food.
- Replace walks, human contact, training, veterinary care, or supervision.

---

## 6. Physical product overview

### 6.1 Main body

- Wall-mounted cream, rounded character form.
- Soft-touch, wipe-clean exterior with hidden fasteners.
- Structural rear chassis transfers pulling loads to the wall mount.
- Front shell does not carry primary pull loads.
- Low-voltage power enters through a protected cable route.

### 6.2 Central boop pad

The large sage circle in the center is the primary boop pad. It is not one of the five modular nodes.

Required capabilities:

- Nose- and paw-sized active area.
- Small, perceptible physical travel.
- Force or pressure sensing across the full surface.
- Soft, wipe-clean skin.
- Edge design that prevents claw or skin pinching.
- Configurable short press, long press, and repeated press.
- Light halo around the perimeter.

The boop pad is appropriate for low-arousal actions such as:

- Start or stop audio.
- Confirm return from a scent game.
- Request attention.
- Cancel or pause an offered activity.
- Acknowledge a learned routine.

### 6.3 Expressive ears

The two soft ears communicate state and delight.

They must:

- Move slowly and within limited travel.
- Use torque-limited actuation.
- Return to neutral after each gesture.
- Never be used as pull handles.
- Stop moving if obstructed.

Example gestures:

- Both neutral: idle.
- Small outward opening: an activity is available.
- One-ear lift: successful action.
- Slow asymmetric wave: familiar person arrived.
- Gradual return downward: session closing.

### 6.4 Camera, microphone, speaker, and lights

- Camera supports dog presence, posture, activity, and event review.
- Microphone supports bark and ambient-audio event detection.
- Speaker provides short, low-volume confirmation sounds and optional audio enrichment.
- Audio exits through protected speaker grilles, not through the boop pad.
- Lights indicate state but are never the only cue.
- Physical availability must remain understandable even if lights or audio are disabled.

---

## 7. Five-node architecture

PawHub v1 has five modular perimeter nodes. The central boop pad is separate and does not count toward the five.

Logical node IDs are fixed in software even if final industrial-design positions shift.

| Node | Nominal position | Primary capability | Typical attachments |
|---|---|---|---|
| N1 | Upper-left | Secondary high-load or owner interaction | Human exercise handle, second resistance strap, owner-confirm button |
| N2 | Upper-right | Low-load tactile input | Choice token, soft ring, release confirmation |
| N3 | Right/lower-right | Low-load utility input | Scent token, fabric tab, soft ball-return sleeve |
| N4 | Five-o'clock/lower-right | Primary dog resistance node | Tug handle, pull-request strap, retracting textile loop |
| N5 | Lower-left | Controlled output | Treat drop, ball roll, harness release, status output |

### 7.1 Attachment visual language

Every active physical attachment uses:

- A flush cream circular puck.
- A small dark rounded-rectangle slot.
- Flat woven webbing or a soft attachment emerging through the slot.

Unused nodes are shallow closed cream or ochre caps.

The discarded green concave or flower-shaped socket must not be used.

### 7.2 Node classes

#### Resistance node

Minimum sensing and actuation:

- Motor or controllable brake.
- Encoder for extension and retraction.
- Load or tension sensing.
- Motor-current sensing.
- Temperature monitoring.
- Mechanical slip or release protection independent of software.
- Controlled, low-speed retraction.

#### Tactile input node

- Low-force switch, displacement sensor, or tension sensor.
- No high-force motorized resistance.
- Attachment identity detection.
- Optional local light.

#### Output node

- Treat metering, ball rolling, or textile-latch release.
- Confirmation sensor for the actual output.
- Jam and obstruction detection.
- Owner-removable, cleanable food path where relevant.

### 7.3 Attachment identification

Each cartridge should report:

- Attachment type.
- Hardware revision.
- Safety class.
- Supported modes.
- Calibration data.
- Service life or cycle count.

The hub must reject an unknown, incompatible, or incorrectly seated attachment and show it as unavailable.

---

## 8. Interaction mode taxonomy

The same pulling motion can mean very different things. Software must explicitly separate the following modes.

### 8.1 Request mode

Purpose: the dog communicates a request such as outside, play, or attention.

Rules:

- One deliberate pull above a calibrated minimum threshold counts.
- Pull magnitude does not increase priority or reward.
- Harder pulling must not produce a better outcome.
- The system confirms the request once, then parks or ignores repeats during cooldown.
- Human confirmation may be required before an output such as harness release.

### 8.2 Resistance play mode

Purpose: time-boxed physical enrichment.

Rules:

- Must begin with an explicit availability cue.
- Resistance adapts only within preconfigured safe limits.
- The dog can release the toy or walk away at any time.
- Resistance must not suddenly increase.
- The session has a duration and repetition limit.
- Completion transitions to a calm release-and-retract sequence.

### 8.3 Together mode

Purpose: cooperative human-and-dog play or exercise using two resistance nodes.

Rules:

- N1 and N4 operate as independent resistance channels.
- The human and dog are never connected by one direct mechanical rope.
- Software synchronizes timing, cues, and progress.
- Each channel retains its own force limit and emergency release.
- An adult starts the session locally.

### 8.4 Choice mode

Purpose: the dog selects between learned tactile options.

Examples:

- Outside.
- Rest.
- Play.

Rules:

- Tokens must have distinct textures and shapes.
- Only one selection is accepted per choice window.
- The selected node confirms; other nodes remain quiet.
- Availability can vary by schedule, but unavailable choices should be physically parked or absent.

### 8.5 Output mode

Purpose: perform a controlled action after a valid request or confirmation.

Examples:

- Dispense one treat.
- Roll one ball along the floor.
- Release a harness onto a mat.

Rules:

- Output must be verified by a sensor.
- Failed output must not be logged as success.
- Repeated input must not repeat an in-progress output.
- Food and release features require configurable daily and session limits.

---

## 9. Availability and on/off behavior

### 9.1 Three separate controls

Developers must not represent all forms of “off” with one boolean.

1. **Device power:** Is the hub powered and healthy?
2. **Feature availability:** Is a specific activity being offered now?
3. **Session state:** Is an offered activity currently being used?

Suggested top-level fields:

- device_state
- feature_availability
- session_state
- node_state
- attachment_state

### 9.2 Core behavioral contract

The dog should learn:

- Visible and accessible attachment plus availability cue means “you may interact.”
- Parked or absent attachment means “this activity is not available.”
- A calm closing sequence means “the activity is finished.”
- Pulling harder never turns an unavailable feature back on.

“Off” is therefore an affordance decision, not a resistance setting.

### 9.3 Pull-session state machine

| State | Physical state | Product cues | Dog interaction | Allowed transition |
|---|---|---|---|---|
| PARKED | Handle retracted or inaccessible | Neutral ears, no invitation light or sound | No reward and no resistance escalation | Owner, schedule, or approved automation may offer |
| OFFERING | Handle slowly becomes accessible | One consistent light, sound, and ear cue | Input ignored until ready | READY after extension and self-test |
| READY | Handle accessible with very low pretension | Availability cue remains subtle | First valid pull starts session | ACTIVE or PARKED on timeout |
| ACTIVE_REQUEST | Stable low resistance | Immediate confirmation | One valid pull creates one request | SUCCESS |
| ACTIVE_PLAY | Bounded adaptive resistance | Rhythmic ear/light feedback | Dog may pull, release, or leave | SUCCESS, COOLDOWN, or FAULT |
| SUCCESS | Output or confirmation occurs once | Single positive cue | Repeats do not create duplicate output | COOLDOWN |
| COOLDOWN | Resistance falls toward zero | Slow closing cue | Interaction is not rewarded | Wait for release, then RETRACTING |
| RETRACTING | Strap retracts slowly after release | Neutralizing cue | Motor stops if tension returns | PARKED |
| LOCKOUT | Attachment parked | Neutral state | Attempts are logged only | PARKED until configured limit expires |
| FAULT | Motor de-energized or mechanically released | Distinct owner-facing alert | No active resistance | Owner inspection and reset |

### 9.4 Required state transitions

1. PARKED to OFFERING requires:
   - Compatible attachment.
   - Valid calibration.
   - No hardware fault.
   - Schedule and daily limit allow the activity.
   - Any required human-presence rule is satisfied.

2. READY to ACTIVE_REQUEST requires:
   - Force above the learned minimum.
   - Pull duration within a valid range.
   - No current lockout.

3. READY to ACTIVE_PLAY requires:
   - Explicit play-session start.
   - Attachment extended and unobstructed.
   - Dog has voluntarily taken the handle.

4. ACTIVE to COOLDOWN occurs on:
   - Completed repetition or request.
   - Session timeout.
   - Owner stop.
   - Dog release or departure.
   - Repeated frantic interaction.
   - Elevated device temperature or current.

5. COOLDOWN to RETRACTING occurs only after release is detected.

### 9.5 What the product must never do

- Increase resistance because the feature is unavailable.
- Reward the strongest pull.
- Retract a strap forcefully while it is still held.
- Change the rule halfway through a pull.
- Dispense repeatedly in response to rapid repeated pulls.
- Begin a high-resistance session from an ML guess.
- Treat barking as a request unless the owner explicitly trains that behavior.
- Use a flashing or repeated sound loop to frustrate the dog into interacting.

### 9.6 Frustration and arousal response

Signals such as rapid repeated pulls, persistent biting near the node, repeated barking, or unusually high force may indicate excitement, confusion, or frustration. They are not reliable diagnoses.

When the rule-based system detects escalation:

1. Resistance must taper down.
2. The system waits for release.
3. The attachment retracts.
4. The feature enters lockout.
5. The owner receives a factual notification.
6. The app may recommend reducing duration or retraining the cue.

The message should say what was observed, not claim an emotion. Example: “Five high-force pulls occurred within 20 seconds after the session ended.”

### 9.7 Training sequence for a new pull attachment

1. **Association:** Owner presents the available handle and rewards calm investigation.
2. **Simple action:** A light pull causes immediate confirmation.
3. **Release:** Owner teaches a release cue; the hub waits for release before retracting.
4. **Short session:** Add only a few low-resistance repetitions.
5. **Closing cue:** Use the same calm sound, ear gesture, and retraction every time.
6. **Unavailability:** Introduce the parked state only after the dog understands the availability cue.
7. **Personalization:** Adjust thresholds gradually using observed successful interactions.

The onboarding flow should require owner confirmation after each stage.

---

## 10. Feature set

### 10.1 MVP

#### Central boop and audio

- Dog presses the central pad.
- Hub confirms through light and a small ear gesture.
- Optional audio starts.
- A second press stops it.
- Owner configures content and maximum volume.

#### Pull request

- Dog performs one low-force pull.
- Hub records one request.
- Owner receives a notification or local cue.
- Feature enters cooldown; harder or repeated pulls do not increase urgency.

#### Controlled treat drop

- A valid trained action requests one treat.
- Rotary mechanism meters one unit.
- Sensor verifies the treat exited.
- Treat falls onto a washable floor mat.
- Daily, hourly, and session limits are enforced.

#### Walk request and harness release

- Dog boops or selects the learned walk token.
- Harness remains secured.
- A person who is physically present confirms.
- Textile loop releases and harness drops onto a defined mat.
- Release never occurs solely from the dog's repeated input.

#### Arrival greeting

- Door, phone proximity, and camera signals identify a likely familiar arrival.
- Hub performs one slow ear wave and one warm light pulse.
- Gesture returns to neutral.
- Owner may disable camera-based greeting.

#### Monitoring and daily summary

- Detect periods of rest, movement, hub interaction, barking, and owner arrival.
- Generate a factual timeline.
- Attach selected short clips only with owner permission.
- Notify only on configured or unusual events.

### 10.2 Post-MVP extensions

#### Together Mode

Human exercise handle and dog tug use two independent resistance nodes with synchronized cues.

#### My Choice

Multiple textured tokens represent outside, rest, or play.

#### Scent Quest

A familiar washable scent token supports a hide-and-find game without food.

#### Roll Again

Dog returns a soft ball through a collapsible sleeve; hub rolls it back along the floor.

#### Tidy Together

Hub cues the dog to place toys in a soft wireless sensing basket and confirms the completed deposit.

---

## 11. Mobile app requirements

### 11.1 Onboarding

The app collects:

- Dog name and profile image.
- Approximate size, age, and activity level.
- Relevant mobility limitations.
- Known guarding, chewing, or pull-fixation concerns.
- Typical daily schedule.
- Owner notification preferences.
- Camera and audio privacy choices.

### 11.2 Attachment setup

For each installed attachment, the app must show:

- Detected attachment type and node.
- Assigned meaning.
- Mode: request, play, choice, or output.
- Availability schedule.
- Required human confirmation.
- Reward and session limits.
- Calibration status.

The system must not guess the meaning of a newly attached module. The owner explicitly assigns it.

### 11.3 Availability controls

Owners can configure:

- Always unavailable.
- Manually offered.
- Offered during selected time windows.
- Offered only while a person is home.
- Offered following a specific routine.
- Maximum sessions per day.
- Minimum cooldown.
- Quiet hours.

### 11.4 Live controls

- Offer or park an activity.
- End an active session.
- Emergency motor stop.
- Disable dispensing.
- Disable camera or microphone according to policy.
- View current node, attachment, and fault states.

### 11.5 Notifications

Notifications should be event-based and factual.

Examples:

- “Milo selected Outside at 4:12 PM.”
- “The tug session ended after 42 seconds.”
- “Three repeated interactions occurred while Outside was unavailable.”
- “Treat output was requested but not confirmed. Check the dispenser.”

Avoid:

- “Milo is angry.”
- “Milo is starving.”
- “Milo is depressed.”

---

## 12. ML system

### 12.1 ML responsibilities

ML may assist with:

- Dog presence and identity.
- Resting, walking, pacing, play, and hub-interaction classification.
- Bark-event detection and clustering.
- Identifying which dog interacted in multi-dog homes.
- Personalized pull thresholds from successful sessions.
- Detecting deviations from the dog's normal interaction pattern.
- Selecting factual events for the daily summary.
- Suggesting schedule or difficulty changes to the owner.

### 12.2 ML non-responsibilities

ML must not:

- Directly control the mechanical maximum force.
- Disable the mechanical slip or emergency release.
- Diagnose emotion, aggression, pain, hunger, or illness.
- Start high-resistance play without deterministic permission.
- Dispense beyond hard product limits.
- Release a harness without the required human confirmation.
- Convert a low-confidence vision prediction into an urgent claim.

### 12.3 Sensor inputs

- Camera frames or on-device embeddings.
- Microphone event features.
- Boop-pad force and duration.
- Node force, extension, velocity, and motor current.
- Attachment identity.
- Speaker, light, and ear-command history.
- Mobile app commands.
- Door or phone-presence integrations where enabled.
- Time, schedule, and session context.

### 12.4 Ground-truth strategy

High-confidence mechanical events should anchor labels:

- Pull started.
- Pull released.
- Boop detected.
- Attachment extended.
- Treat confirmed.
- Ball return confirmed.
- Harness release confirmed.
- Owner confirmation received.

Owner feedback supplies:

- Correct dog identity.
- Correct activity label.
- False notification.
- Useful or unhelpful daily-summary event.
- Acceptable session difficulty.

Video-only inferred events should carry confidence and never overwrite sensor-confirmed facts.

### 12.5 Model rollout

#### Phase 0 — deterministic baseline

- No adaptive behavior.
- Fixed owner-configured thresholds.
- Full event logging.
- Establish reliable state machines and safety behavior.

#### Phase 1 — perception

- Dog presence.
- Hub approach.
- Rest, movement, and interaction classification.
- Bark-event detection.

#### Phase 2 — personalization

- Per-dog valid-pull threshold.
- Typical session duration.
- Normal interaction frequency.
- Notification sensitivity.

#### Phase 3 — summaries and recommendations

- Generate summaries only from verified structured events.
- Use generative language for presentation, not for inventing events.
- Recommendations require owner approval.

### 12.6 Initial evaluation targets

Targets should be validated against pilot data:

- Sensor-confirmed node interaction detection: at least 95% recall.
- Dog-presence model: at least 0.90 F1 in supported lighting.
- Correct dog identity in supported multi-dog homes: target at least 90%.
- Fewer than one false urgent notification per dog per day after calibration.
- At least 95% factual precision for events included in daily summaries.
- Zero model-initiated violations of hard session, dispensing, or force limits.

Performance must also be reported by:

- Dog size and coat.
- Lighting condition.
- Camera angle.
- Single- versus multi-dog household.
- Attachment type.

---

## 13. Event and data model

Every interaction should produce a structured event with:

- event_id
- timestamp
- household_id
- hub_id
- dog_id or unknown
- node_id
- attachment_type
- attachment_revision
- mode
- device_state
- feature_availability
- session_state
- input_type
- force_peak
- pull_duration
- extension_distance
- output_requested
- output_confirmed
- rule_triggered
- model_labels and confidence
- owner_command
- media_reference, if permitted
- outcome
- fault_code

### 13.1 Suggested core events

- HUB_ONLINE
- HUB_OFFLINE
- ATTACHMENT_CONNECTED
- ATTACHMENT_REJECTED
- FEATURE_OFFERED
- FEATURE_PARKED
- BOOP
- PULL_START
- PULL_VALID
- PULL_RELEASE
- REQUEST_CREATED
- SESSION_STARTED
- SESSION_ENDED
- SESSION_LOCKED_OUT
- OUTPUT_REQUESTED
- OUTPUT_CONFIRMED
- OUTPUT_FAILED
- HUMAN_CONFIRMED
- OVERFORCE
- JAM
- EMERGENCY_RELEASE
- DOG_DETECTED
- BARK_EVENT
- ARRIVAL_DETECTED
- OWNER_FEEDBACK

### 13.2 Session record

A session joins multiple events and contains:

- session_id
- intended feature
- start reason
- end reason
- active node set
- configured limits
- repetitions
- maximum observed force
- number of releases
- number of ignored repeat inputs
- output count
- safety interventions
- owner feedback

---

## 14. Safety requirements

### 14.1 Mechanical

- Primary pull loads transfer to a structural wall plate.
- Installation instructions specify compatible wall types and anchors.
- Mechanical slip protection works without power.
- Strap retraction stops when unexpected tension is detected.
- No accessible pinch, shear, or gear points.
- Dog-accessible components are rounded and bite-resistant.
- Textile parts are replaceable and inspectable.
- No rigid hook protrudes into the dog's path.

### 14.2 Software

- Hard limits are stored locally and continue without cloud connectivity.
- Watchdog stops motors on control-loop failure.
- Commands are idempotent where duplicate output could be harmful.
- A failed sensor moves the affected node to unavailable, not degraded active operation.
- Firmware update failure cannot leave a motor energized.
- Event timestamps and state transitions are auditable.

### 14.3 Food

- Food-contact parts separate from motors and electronics.
- Washable parts are removable without tools.
- Treat size and compatibility are checked during setup.
- Dispensing limits cannot be bypassed by repeated interaction.
- A failed drop does not automatically attempt unlimited retries.

### 14.4 Behavioral

- Consistent availability, success, cooldown, and closing cues.
- No punishment mode.
- No escalating resistance outside play.
- No unpredictable mid-session rules.
- Owner onboarding includes release-cue training.
- Beta program requires review by a qualified canine behavior professional.

The product may reduce ambiguity and frustration, but it cannot guarantee that a dog will never become over-aroused or aggressive.

---

## 15. Privacy and security

- Edge processing is preferred for continuous camera and microphone analysis.
- Raw video or audio upload is opt-in.
- Daily summaries reference verified events even if media storage is disabled.
- Owners can delete media and interaction history.
- Visible product state should indicate when live viewing is active.
- Device identity, app commands, and firmware updates require authenticated encryption.
- Staff access to household media requires explicit support authorization and audit logs.

---

## 16. Success metrics

### Adoption

- Percentage of installed attachments successfully configured.
- Percentage of households completing training onboarding.
- Weekly active dogs and weekly active owners.

### Interaction quality

- Valid interactions per offered session.
- Release success rate.
- Sessions ended voluntarily.
- Repeat inputs during cooldown.
- Lockouts and safety interventions.

### Communication value

- Owner-confirmed useful requests.
- Percentage of requests receiving a human response.
- Reduced repeat requests after confirmation.

### Reliability

- Output confirmation rate.
- Attachment recognition success.
- Jam rate.
- Motor or sensor fault rate.
- Daily-summary factual accuracy.

### Welfare guardrails

- High-force events per active hour.
- Repeated-interaction events after session close.
- Owner-reported avoidance, fixation, or guarding.
- Dropout rate during onboarding.

Welfare guardrails are release criteria, not engagement metrics to maximize.

---

## 17. MVP acceptance criteria

The MVP is ready for a controlled household pilot when:

1. All five node IDs and compatible attachment classes are recognized reliably.
2. The hub distinguishes PARKED, READY, ACTIVE, COOLDOWN, and FAULT locally.
3. An unavailable pull feature cannot increase motor resistance in response to pulling.
4. A request produces only one event and one permitted output during its cooldown.
5. Strap retraction waits for release and stops on unexpected tension.
6. Mechanical overforce protection functions without software or network access.
7. Treat output is sensor-confirmed and limited.
8. Harness release requires human confirmation.
9. The app shows the actual node, attachment, availability, and session state.
10. Daily summaries contain only verified or confidence-labeled events.
11. Owners can disable camera, audio, dispensing, and resistance modes.
12. Faults are logged, surfaced, and leave the affected node unavailable.
13. Canine behavior and mechanical safety reviews are complete for the pilot protocol.

---

## 18. Development phases

### Phase A — simulator and bench hardware

- Implement the state machine without ML.
- Simulate all five nodes and attachment identities.
- Test duplicate commands, sensor loss, power loss, overforce, and jams.
- Establish event schemas and logging.

### Phase B — supervised prototype

- Central boop.
- One resistance node.
- One tactile input node.
- One controlled output node.
- App setup and emergency stop.
- Human-supervised training only.

### Phase C — limited household pilot

- Five-node prototype.
- Deterministic schedules and limits.
- Monitoring, notifications, and factual timeline.
- No autonomous resistance personalization.

### Phase D — ML-assisted pilot

- Dog presence and interaction classification.
- Personalized thresholds within fixed bounds.
- Daily summaries.
- Owner-approved recommendations.

### Phase E — extension ecosystem

- Together Mode.
- My Choice.
- Scent Quest.
- Roll Again.
- Tidy Together.

---

## 19. Open decisions

Product, engineering, and behavior teams must resolve:

1. Final rated load and travel for N1 and N4 by dog-size class.
2. Whether N1 is high-load in every hub or enabled only with an upgraded wall mount.
3. Exact physical mechanism used to hide or park an unavailable handle.
4. Whether a request attachment retracts fully or is covered by a sliding soft door.
5. Default cooldowns for each feature.
6. Required human-presence evidence for harness release and Together Mode.
7. Supported treat dimensions and cleaning method.
8. Whether ball return belongs in the hub or a paired floor accessory.
9. Multi-dog identity and conflict-handling rules.
10. Retention policy for raw media, event data, and embeddings.
11. Minimum validated behavior-training protocol before unsupervised use.
12. Certification and regional regulatory plan.

---

## 20. Visual references

- design/DESIGN_CANON.md
- design/hub-v7-story-tug-reward.png
- design/hub-v7-story-walk-request.png
- design/hub-v7-story-day-in-life.png
- design/hub-v8-together-mode.png
- design/hub-v8-my-choice.png
- design/hub-v8-scent-quest.png
- design/hub-v8-roll-again.png
- design/hub-v8-tidy-together.png

---

## 21. Product decisions summary

1. There are five modular perimeter nodes; the central boop pad is separate.
2. Pulling is divided into request mode and resistance-play mode.
3. Pull force is not interpreted as hunger, urgency, or emotional intensity.
4. Harder pulling never creates a better reward.
5. “Off” means the attachment is parked or unavailable, not harder to move.
6. High resistance exists only during a clearly offered, bounded play session.
7. Human and dog channels in Together Mode are independent.
8. Food, harness release, and other outputs are limited and sensor-confirmed.
9. ML recommends and personalizes inside deterministic constraints.
10. Safety and understandable behavior take priority over engagement.
