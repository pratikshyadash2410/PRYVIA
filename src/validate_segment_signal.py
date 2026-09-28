# src/validate_segment_signal.py

import pandas as pd


# ============================================================
# LOAD DATA
# ============================================================

users = pd.read_csv(
    "users_prototype.csv"
)

assignments = pd.read_csv(
    "experiment_assignments_prototype.csv"
)

sessions = pd.read_csv(
    "search_sessions_prototype.csv"
)

success = pd.read_csv(
    "search_success_prototype.csv"
)


# ============================================================
# BUILD SEARCH → USER → DEVICE → VARIANT
# ============================================================

search_user = sessions[
    [
        "session_id",
        "user_id",
    ]
].copy()

data = success.merge(
    search_user,
    on="session_id",
    how="left",
)

data = data.merge(
    users[
        [
            "user_id",
            "device_type",
        ]
    ],
    on="user_id",
    how="left",
)

data = data.merge(
    assignments[
        [
            "experiment_id",
            "user_id",
            "variant",
        ]
    ],
    on="user_id",
    how="inner",
)


# ============================================================
# EXPERIMENT 3 ONLY
# ============================================================

exp3 = data[
    data["experiment_id"] == 3
].copy()


# ============================================================
# SEGMENT SSR
# ============================================================

segment_ssr = (
    exp3
    .groupby(
        [
            "device_type",
            "variant",
        ]
    )["successful_search"]
    .mean()
    .unstack()
    * 100
)


print()
print("=" * 70)
print("PRYVIA — EXPERIMENT 3 SEGMENT VALIDATION")
print("=" * 70)

print()
print("SSR by device and variant:")

print(
    segment_ssr.round(2)
)


# ============================================================
# SEGMENT LIFTS
# ============================================================

mobile_lift = (
    segment_ssr.loc[
        "Mobile",
        "Treatment",
    ]
    -
    segment_ssr.loc[
        "Mobile",
        "Control",
    ]
)

desktop_lift = (
    segment_ssr.loc[
        "Desktop",
        "Treatment",
    ]
    -
    segment_ssr.loc[
        "Desktop",
        "Control",
    ]
)


print()

for device, lift in [
    ("Mobile", mobile_lift),
    ("Desktop", desktop_lift),
]:

    control = segment_ssr.loc[
        device,
        "Control",
    ]

    treatment = segment_ssr.loc[
        device,
        "Treatment",
    ]

    print(device)
    print("-" * 30)

    print(
        f"Control SSR:   {control:.2f}%"
    )

    print(
        f"Treatment SSR: {treatment:.2f}%"
    )

    print(
        f"Lift:          {lift:+.2f} pp"
    )


# ============================================================
# INTERACTION EFFECT
# ============================================================

interaction = (
    mobile_lift
    - desktop_lift
)


print()
print("=" * 70)
print("SEGMENT INTERACTION")
print("=" * 70)

print(
    f"Mobile lift:     {mobile_lift:+.2f} pp"
)

print(
    f"Desktop lift:    {desktop_lift:+.2f} pp"
)

print(
    f"Interaction:     {interaction:+.2f} pp"
)


# ============================================================
# INTERPRETATION
# ============================================================

print()
print("=" * 70)
print("INTERPRETATION")
print("=" * 70)


# We deliberately do NOT require Desktop to be exactly zero.
#
# Why?
# A segment experiment can reveal:
#
#   Mobile  → positive
#   Desktop → neutral
#
# OR:
#
#   Mobile  → positive
#   Desktop → negative
#
# Both represent heterogeneous treatment effects.
#
# The key requirement is that the treatment effect differs
# materially between the segments.

if (
    mobile_lift >= 3.0
    and interaction >= 5.0
):

    print(
        "PASS — strong heterogeneous treatment "
        "effect detected."
    )

    print(
        f"Mobile shows a {mobile_lift:+.2f} pp "
        "SSR effect."
    )

    print(
        f"The Mobile-vs-Desktop treatment interaction "
        f"is {interaction:+.2f} pp."
    )

    print()
    print(
        "IMPORTANT: Segment results are exploratory "
        "and are NOT used by the decision engine."
    )

else:

    print(
        "FAIL — segment interaction is not strong "
        "enough for the intended scenario."
    )