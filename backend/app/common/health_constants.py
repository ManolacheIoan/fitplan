"""Every health-related threshold and coefficient used by FitPlan, in one place.

!!! These values are PLACEHOLDERS chosen from commonly cited defaults. They MUST be
!!! reviewed and approved by a qualified professional (physician / registered
!!! dietitian) before the application is used by the public.

Formulas using these constants live in app/nutrition/rules.py and
app/profile/screening.py. Training volume constants live in app/plans/constants.py.
"""

from typing import Final

# --- Eligibility ---------------------------------------------------------------------------
# The application is for adults only.
MIN_AGE_YEARS: Final = 18
# Upper bound of the accepted input range (data sanity, not a medical statement).
MAX_AGE_YEARS: Final = 100

# --- Body mass index -------------------------------------------------------------------------
# Weight-loss goals are blocked below this BMI (kg/m²). 18.5 is the WHO cut-off for
# "underweight". To validate: should there be a safety margin above the cut-off?
BMI_MIN_FOR_WEIGHT_LOSS: Final = 18.5

# --- Basal metabolic rate: Mifflin-St Jeor (1990) -------------------------------------------
# BMR = 10 * weight_kg + 6.25 * height_cm - 5 * age_years + sex_constant
MIFFLIN_WEIGHT_COEF: Final = 10.0
MIFFLIN_HEIGHT_COEF: Final = 6.25
MIFFLIN_AGE_COEF: Final = 5.0
MIFFLIN_SEX_CONSTANT: Final = {"male": 5.0, "female": -161.0}

# --- Activity multipliers (TDEE = BMR * multiplier) --------------------------------------
ACTIVITY_MULTIPLIERS: Final = {
    "sedentary": 1.2,  # little or no exercise, desk job
    "light": 1.375,  # light exercise 1-3 days/week
    "moderate": 1.55,  # moderate exercise 3-5 days/week
    "active": 1.725,  # hard exercise 6-7 days/week
    "very_active": 1.9,  # physical job plus hard exercise
}

# --- Energy adjustment by goal ---------------------------------------------------------------
# Fraction of TDEE removed (lose) or added (gain) before the weekly-rate caps below apply.
DEFICIT_FRACTION: Final = 0.20
SURPLUS_FRACTION: Final = 0.10
# Maximum expected weekly change, as a fraction of body weight. The deficit/surplus is
# capped so that the estimated rate does not exceed these values.
MAX_WEEKLY_LOSS_FRACTION: Final = 0.0075
MAX_WEEKLY_GAIN_FRACTION: Final = 0.0025
# Approximate energy content of 1 kg of body-mass change (itself an approximation).
KCAL_PER_KG_BODY_MASS: Final = 7700.0

# --- Calorie floor ---------------------------------------------------------------------------
# Targets are never set below these values (kcal/day).
CALORIE_FLOOR: Final = {"male": 1500, "female": 1200}

# --- Macronutrients --------------------------------------------------------------------------
# Protein in grams per kg of (total) body weight. To validate: at high BMI an adjusted or
# reference body weight may be more appropriate than total body weight.
PROTEIN_G_PER_KG: Final = {"lose": 2.0, "maintain": 1.6, "gain": 1.8}
# Minimum share of calories from fat.
MIN_FAT_FRACTION: Final = 0.25
# Energy density (kcal per gram) - standard Atwater factors.
KCAL_PER_G_PROTEIN: Final = 4.0
KCAL_PER_G_CARB: Final = 4.0
KCAL_PER_G_FAT: Final = 9.0

# --- Data-entry ranges (input sanity, not medical thresholds) -----------------------------
HEIGHT_CM_RANGE: Final = (120.0, 230.0)
WEIGHT_KG_RANGE: Final = (30.0, 300.0)
