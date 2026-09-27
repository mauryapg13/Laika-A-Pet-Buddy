# Laika hardware

The physical hub: what it is made of, what each part senses and does, how it stays safe, and how it talks to the
software. This is summarised from the [product requirements](PRD.md) (§6, §7, §12.3, §14). For how the software
treats each input, see the [hub reference](hub.md).

![The hub in use: notice, pull, response, reward](images/04_tug_treat_reward.jpeg)

## 1. The body

- **Shape and finish:** a wall-mounted, rounded, cream "character" form with a soft-touch, wipe-clean shell and
  hidden fasteners.
- **Structure:** a rear chassis carries pulling loads into a structural wall plate. The front shell never takes the
  main pull load.
- **Power:** low-voltage power enters through a protected cable route.

### Central boop pad
The large sage circle in the middle. It is separate from the five nodes.
- **Surface:** a nose- and paw-sized area with a little physical travel, and force/pressure sensing across all of it.
- **Build:** a soft, wipe-clean skin, and an edge designed so it can't pinch claws or skin.
- **Presses:** short, long and repeated presses can each mean something different.
- **Halo:** a light ring around the edge shows state.
- **Use:** low-arousal actions, such as asking for a walk, starting or stopping calm audio, or asking for attention.

### Ears
Two soft ears show state and delight: small opening = activity available, one-ear lift = success, slow wave =
someone familiar arrived.
- **Motion:** slow, limited travel with torque-limited actuators. They return to neutral after every gesture.
- **Safety:** they stop if obstructed, and they are never pull handles.

### Camera, microphone, speaker, lights
- **Camera:** dog presence, posture and activity. The software side is [`backend/laika/camera/`](../backend/laika/camera/).
- **Microphone:** bark and ambient-sound events.
- **Speaker:** short, quiet confirmation sounds and optional calm audio. Sound comes out through protected grilles,
  not the boop pad.
- **Lights:** show state but are never the only cue. The hub must stay understandable with lights or sound off.

## 2. Five modular nodes

Five sockets sit around the edge. Each takes a swappable attachment (a flush cream puck with a slot, and soft
webbing coming out of it). Unused sockets are closed with plain caps. Node IDs are fixed in software.

| Node | Position | Class | In the current software | Example attachments |
|---|---|---|---|---|
| **BOOP** | centre | boop pad | walk request | built in |
| **N1** | upper left | input | owner's Yes / confirm button, tidy cue | owner button, second strap |
| **N2** | upper right | tactile input | calm audio on/off | soft ring, choice token |
| **N3** | left side | tactile input | ball return pocket (Roll Again) | fabric tab, ball-return sleeve |
| **N4** | lower right | **resistance** | tug strap, harness holder, choice tokens | tug handle, pull strap, textile loop |
| **N5** | lower left | **output** | treat drop, ball roll-out | treat dispenser, ball roller, harness release |

### What each node class needs

| Class | Sensing | Actuation and protection |
|---|---|---|
| **Resistance** (N4) | load/tension sensor, encoder for extension and retraction, motor current, temperature | motor or controllable brake, slow controlled retraction, mechanical slip/release that works without software |
| **Tactile input** (N1–N3) | low-force switch, displacement or tension sensor, attachment identity | no motorised resistance; optional local light |
| **Output** (N5) | a sensor that confirms the output actually happened, jam/obstruction detection | treat metering, ball rolling or textile-latch release; food path removable and washable |

### Attachment identification
Each attachment cartridge reports:
- its type, hardware revision and safety class;
- the modes it supports;
- its calibration data and cycle count.

The hub rejects unknown, incompatible or badly seated attachments and shows them as unavailable.

## 3. Safety by design

**Mechanical**
- Pull loads go into a structural wall plate, with specified wall types and anchors.
- Slip protection works with the power off.
- Retraction stops on unexpected tension.
- There are no accessible pinch, shear or gear points, and no rigid hooks in the dog's path.
- Dog-reachable parts are rounded and bite-resistant; textiles are replaceable.

**Food**
- Food-contact parts are separate from motors and electronics, and removable for washing without tools.
- Treat size is checked at setup.
- Dispensing limits can't be bypassed by repeated interaction.
- A failed drop is never retried endlessly.

**Firmware**
- Hard limits live on the device and keep working without the cloud.
- A watchdog stops the motors if the control loop fails.
- A failed sensor makes its node unavailable rather than half-working.
- A failed firmware update can never leave a motor energised.

These map directly onto the software rules: stronger pulls never win, "off" means the strap retracts rather than
gets harder to pull, and outputs only count once their sensor confirms them. See [hub.md §3](hub.md#3-safety-rules-always-on-no-ml-involved).

## 4. How the hardware talks to the software

The hub's brain ([`backend/laika/hub/`](../backend/laika/hub/)) is hardware-agnostic: JSON in, JSON out.

- **Sensors → software.** The microcontroller turns each sensor reading into an input and posts it to `POST /input`
  (for example, over USB serial through a small bridge script):
  ```json
  {"type": "pull", "node": "N4", "force": 5.1, "duration_ms": 600}
  {"type": "boop", "duration_ms": 300}
  {"type": "ball_in"}
  {"type": "output_confirmed", "node": "N5"}
  ```
- **Software → actuators.** Every response has an `actions` list for the hardware to carry out, such as
  `dispense_treat` (N5), `extend_strap` / `retract_strap` (N4), `release_harness`, `ear_wave`, `halo_pulse`,
  `play_sound` and `stop_motors`. The hardware then reports `output_confirmed` or `output_failed`.
- **Ears and halo:** each response also carries an `ears` and a `halo` value for the current moment.

The full list of inputs, actions and gestures is in [hub.md §5–6](hub.md#5-json-contract-inputs).

## 5. Status

- **Hardware work:** prototype development, hardware testing and integration are led by Ankit Kumar.
- **Software:** it does not drive the physical prototype yet. It runs against the same JSON a real sensor bridge
  would send; in demos, a simulated sensor confirms each output.
- **Next step:** connecting the prototype means writing that bridge. The rules and the web app already work.
