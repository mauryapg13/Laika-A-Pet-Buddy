"""Hard limits and the physical layout of the hub. Safety rules live here, not in ML."""

LIMITS = {
    # treats (Tug -> Treat)
    "treats_per_day": 8,
    "treats_per_hour": 3,
    "pulls_per_treat": 6,
    # valid pull (magnitude above threshold is ignored - harder never means better)
    "pull_min_ms": 200,
    "pull_max_ms": 4000,
    "threshold_default_n": 3.0,
    "threshold_bounds_n": (2.0, 8.0),
    # tug session
    "tug_session_max_s": 180,
    "resistance_max": 3,
    # frustration guard: this many high-force pulls within the window -> lockout
    "frantic_pulls": 5,
    "frantic_window_s": 20,
    "frantic_force_n": 12.0,
    "lockout_s": 600,
    # requests
    "walk_cooldown_s": 120,
    "request_expiry_s": 600,
    "choice_window_s": 60,
    # roll again
    "rolls_per_session": 10,
    "roll_gap_s": 3,
    "roll_idle_timeout_s": 120,
    # tidy together
    "tidy_window_s": 120,
    # arrival greeting
    "human_confidence_min": 0.7,
    "greet_cooldown_s": 600,
    # audio enrichment
    "audio_max_s": 1800,
    # ML suggestion
    "idle_suggest_s": 7200,
}

# Front view of the hub (see README / PLAN for the picture)
NODES = {
    "BOOP": "Central boop pad (dog) - walk request; halo light around it",
    "N1": "Upper-left yellow button (owner) - Confirm / Yes, Tidy cue",
    "N2": "Upper-right cream button (dog) - audio enrichment on/off",
    "N3": "Left side button + pocket (dog) - ball return sleeve",
    "N4": "Lower-right strap (dog) - bone tug / harness holder / choice tokens",
    "N5": "Lower-left yellow spout (output) - treat drop / ball roll-out",
}

# My Choice: owner-assigned meaning of each textured token (matches the wooden cards)
CHOICES = {
    "C_LEFT": {"token": "blue_rope", "meaning": "OUTSIDE"},
    "C_CENTER": {"token": "paw_strap", "meaning": "REST"},
    "C_RIGHT": {"token": "yellow_ring", "meaning": "PLAY"},
}

# What gets clipped to the strap (N4) for each offered feature
ATTACHMENT_FOR = {"tug": "bone_tug", "walk": "harness", "choice": "choice_tokens"}
FEATURES = ("tug", "walk", "choice", "roll", "tidy")
